"""
api/meeting_routes.py - Routes des réunions
POST   /api/meetings
GET    /api/meetings
GET    /api/meetings/{id}
PUT    /api/meetings/{id}
DELETE /api/meetings/{id}
GET    /api/meetings/{id}/status   (polling du traitement)
GET    /api/stats                   (tableau de bord)
POST   /api/reprocess/{id}         (retraitement)
"""

from flask import Blueprint, jsonify, request

from middleware.jwt import jwt_required
from services.meeting_service import MeetingService

meeting_bp = Blueprint("meetings", __name__)


@meeting_bp.route("/meetings", methods=["POST"])
@jwt_required
def create_meeting(current_user):
    """Crée une nouvelle réunion."""
    data = request.get_json(silent=True) or {}
    response, status = MeetingService.create_meeting(current_user, data)
    return jsonify(response), status


@meeting_bp.route("/meetings", methods=["GET"])
@jwt_required
def get_all_meetings(current_user):
    """
    Liste les réunions de l'utilisateur.
    Paramètres query : status, search, sort_by, sort_dir
    """
    response, status = MeetingService.get_all_meetings(current_user, request.args)
    return jsonify(response), status


@meeting_bp.route("/meetings/<int:meeting_id>", methods=["GET"])
@jwt_required
def get_meeting(current_user, meeting_id: int):
    """Retourne le détail complet d'une réunion."""
    response, status = MeetingService.get_meeting(current_user, meeting_id)
    return jsonify(response), status


@meeting_bp.route("/meetings/<int:meeting_id>", methods=["PUT"])
@jwt_required
def update_meeting(current_user, meeting_id: int):
    """Met à jour le titre ou la description."""
    data = request.get_json(silent=True) or {}
    response, status = MeetingService.update_meeting(current_user, meeting_id, data)
    return jsonify(response), status


@meeting_bp.route("/meetings/<int:meeting_id>", methods=["DELETE"])
@jwt_required
def delete_meeting(current_user, meeting_id: int):
    """Supprime la réunion et toutes ses données liées."""
    response, status = MeetingService.delete_meeting(current_user, meeting_id)
    return jsonify(response), status


@meeting_bp.route("/meetings/<int:meeting_id>/status", methods=["GET"])
@jwt_required
def get_meeting_status(current_user, meeting_id: int):
    """
    Retourne l'état du traitement en temps réel.
    Endpoint pour le polling côté frontend.
    Équivalent de GET /api/jobs/{meeting_id} du cahier des charges.
    """
    response, status = MeetingService.get_processing_status(current_user, meeting_id)
    return jsonify(response), status


@meeting_bp.route("/stats", methods=["GET"])
@jwt_required
def get_stats(current_user):
    """
    Retourne les statistiques pour le tableau de bord :
    total réunions, terminées, en traitement, durée totale, dernière réunion.
    """
    response, status = MeetingService.get_dashboard_stats(current_user)
    return jsonify(response), status


@meeting_bp.route("/reprocess/<int:meeting_id>", methods=["POST"])
@jwt_required
def reprocess_meeting(current_user, meeting_id: int):
    """
    Retraite une réunion sans la réenregistrer.
    Utile pour tester un nouveau prompt ou un nouveau modèle.
    La transcription déjà stockée est réutilisée.
    """
    from services.billing_service import BillingService

    entitlement = BillingService.entitlement(current_user, "report")
    if entitlement:
        response, status = entitlement
        return jsonify(response), status
    from services.organization_service import OrganizationService
    if not OrganizationService.can_organize(current_user):
        return jsonify({"error": "Votre rôle ne permet pas de retraiter une réunion."}), 403
    #from workers.transcription_worker import start_processing_pipeline
    from flask import current_app

    from models.Meeting import MeetingStatus
    from repositories.meeting_repository import MeetingRepository
    from repositories.summary_repository import SummaryRepository

    meeting = MeetingRepository.find_by_id_and_user(meeting_id, current_user.id)
    if not meeting:
        return jsonify({"error": "Réunion introuvable."}), 404

    transcript = SummaryRepository.get_transcript(meeting_id)
    if not transcript or not transcript.full_text:
        return jsonify({"error": "Aucune transcription disponible pour retraiter."}), 400

    # Remet le statut en cours d'analyse
    MeetingRepository.update_status(meeting, MeetingStatus.ANALYZING,
                                    step="Retraitement en cours", progress=0)

    # Lance uniquement la partie résumé + extraction + RAG (sans Whisper)
    _reprocess_thread(meeting_id, transcript.full_text, current_app._get_current_object())

    return jsonify({
        "message":    "Retraitement lancé.",
        "meeting_id": meeting_id,
    }), 202


def _reprocess_thread(meeting_id: int, transcript_text: str, app) -> None:
    """Lance le retraitement dans un thread séparé."""
    def _run():
        with app.app_context():
            from ai.rag import RAGService
            from ai.summarizer import generate_full_report
            from models.Meeting import MeetingStatus
            from repositories.meeting_repository import MeetingRepository
            from repositories.summary_repository import SummaryRepository

            meeting = MeetingRepository.find_by_id(meeting_id)
            try:
                MeetingRepository.update_status(meeting, MeetingStatus.ANALYZING,
                                                step="Bilan IA", progress=40)
                report = generate_full_report(transcript_text)
                SummaryRepository.save_summary(
                    meeting_id,
                    general_summary=report.get("general_summary",""),
                    participants=report.get("participants",[]),
                    conclusion=report.get("conclusion","")
                )
                SummaryRepository.save_decisions(meeting_id, report.get("decisions", []))
                SummaryRepository.save_actions(meeting_id,   report.get("actions", []))
                SummaryRepository.save_questions(meeting_id, report.get("questions", []))
                SummaryRepository.save_risks(meeting_id,     report.get("risks", []))

                MeetingRepository.update_status(meeting, MeetingStatus.ANALYZING,
                                                step="Indexation RAG", progress=85)
                RAGService.index_meeting(meeting_id, transcript_text, meeting.title)

                MeetingRepository.update_status(meeting, MeetingStatus.COMPLETED,
                                                step="Terminé", progress=100)
            except Exception as e:
                MeetingRepository.update(meeting, status=MeetingStatus.ERROR,
                                         error_message=str(e))

    from workers.transcription_worker import submit_background

    submit_background(_run)
