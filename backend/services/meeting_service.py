"""
services/meeting_service.py - Logique métier des réunions
"""

from repositories.meeting_repository import MeetingRepository
from repositories.summary_repository import SummaryRepository
from schemas.meeting_schema import validate_create_meeting, validate_update_meeting
from utils.file import delete_meeting_files
from services.organization_service import OrganizationService


class MeetingService:

    @staticmethod
    def create_meeting(user, data: dict) -> tuple[dict, int]:
        """Crée une nouvelle réunion pour l'utilisateur."""
        if not OrganizationService.can_organize(user):
            return {"error": "Votre rôle ne permet pas de créer une réunion."}, 403
        from services.billing_service import BillingService
        entitlement = BillingService.entitlement(user, "meeting")
        if entitlement:
            return entitlement
        cleaned, errors = validate_create_meeting(data)
        if errors:
            return {"errors": errors}, 400

        membership = OrganizationService.membership_for(user)
        if not membership:
            return {"error": "Configurez votre espace entreprise avant de créer une réunion.", "code": "ONBOARDING_REQUIRED"}, 428

        meeting = MeetingRepository.create(
            user_id=user.id,
            organization_id=membership.organization_id,
            title=cleaned.get("title"),
            description=cleaned.get("description")
        )
        return {"message": "Réunion créée.", "meeting": meeting.to_dict()}, 201

    @staticmethod
    def get_all_meetings(user, query_params: dict) -> tuple[dict, int]:
        """
        Liste toutes les réunions de l'utilisateur avec filtres.
        Utilisé par le Dashboard et la page Historique.
        """
        status   = query_params.get("status")
        search   = query_params.get("search")
        sort_by  = query_params.get("sort_by", "created_at")
        sort_dir = query_params.get("sort_dir", "desc")

        # Champs de tri autorisés pour éviter les injections
        allowed_sorts = ["created_at", "title", "duration", "status"]
        if sort_by not in allowed_sorts:
            sort_by = "created_at"

        meetings = MeetingRepository.find_all_by_user(
            user_id=user.id,
            status=status,
            search=search,
            sort_by=sort_by,
            sort_dir=sort_dir
        )
        return {"meetings": [m.to_dict() for m in meetings]}, 200

    @staticmethod
    def get_meeting(user, meeting_id: int) -> tuple[dict, int]:
        """Retourne le détail complet d'une réunion."""
        meeting = MeetingRepository.find_by_id_and_user(meeting_id, user.id)
        if not meeting:
            return {"error": "Réunion introuvable."}, 404

        data = meeting.to_dict()

        # Enrichit avec les données IA si disponibles
        transcript = SummaryRepository.get_transcript(meeting_id)
        summary    = SummaryRepository.get_summary(meeting_id)

        if transcript:
            data["transcript"] = transcript.to_dict()
        if summary:
            data["summary"] = summary.to_dict()

        return {"meeting": data}, 200

    @staticmethod
    def update_meeting(user, meeting_id: int, data: dict) -> tuple[dict, int]:
        """Met à jour le titre ou la description d'une réunion."""
        if not OrganizationService.can_organize(user):
            return {"error": "Votre rôle ne permet pas de modifier une réunion."}, 403
        meeting = MeetingRepository.find_by_id_and_user(meeting_id, user.id)
        if not meeting:
            return {"error": "Réunion introuvable."}, 404

        cleaned, errors = validate_update_meeting(data)
        if errors:
            return {"errors": errors}, 400

        meeting = MeetingRepository.update(meeting, **cleaned)
        return {"message": "Réunion mise à jour.", "meeting": meeting.to_dict()}, 200

    @staticmethod
    def delete_meeting(user, meeting_id: int) -> tuple[dict, int]:
        """
        Supprime une réunion et toutes ses données :
        audio, transcription, résumé, embeddings, PDF.
        """
        if not OrganizationService.can_organize(user):
            return {"error": "Votre rôle ne permet pas de supprimer une réunion."}, 403
        meeting = MeetingRepository.find_by_id_and_user(meeting_id, user.id)
        if not meeting:
            return {"error": "Réunion introuvable."}, 404

        # Supprime les fichiers audio sur disque
        delete_meeting_files(meeting_id)

        # Supprime en base (cascade SQLAlchemy pour toutes les relations)
        MeetingRepository.delete(meeting)

        # Supprime les embeddings ChromaDB
        try:
            from ai.rag import RAGService
            RAGService.delete_meeting_embeddings(meeting_id)
        except Exception:
            pass  # Non bloquant

        return {"message": "Réunion supprimée."}, 200

    @staticmethod
    def get_dashboard_stats(user) -> tuple[dict, int]:
        """Retourne les statistiques du tableau de bord."""
        stats = MeetingRepository.get_stats_for_user(user.id)
        return {"stats": stats}, 200

    @staticmethod
    def get_processing_status(user, meeting_id: int) -> tuple[dict, int]:
        """Retourne l'état du traitement en temps réel (pour polling frontend)."""
        meeting = MeetingRepository.find_by_id_and_user(meeting_id, user.id)
        if not meeting:
            return {"error": "Réunion introuvable."}, 404

        return {
            "status":   meeting.status,
            "step":     meeting.processing_step,
            "progress": meeting.processing_progress,
        }, 200
