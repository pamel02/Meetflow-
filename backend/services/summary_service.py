"""
services/summary_service.py - Logique métier pour les données IA
Récupération des résumés, décisions, actions, transcriptions, etc.
"""

from models.Meeting import MeetingStatus
from repositories.meeting_repository import MeetingRepository
from repositories.summary_repository import SummaryRepository


class SummaryService:

    @staticmethod
    def _check_access(user, meeting_id: int):
        """Vérifie que la réunion existe et appartient à l'utilisateur."""
        meeting = MeetingRepository.find_by_id_and_user(meeting_id, user.id)
        if not meeting:
            return None, ({"error": "Réunion introuvable."}, 404)
        return meeting, None

    @staticmethod
    def _check_report_access(user):
        from services.billing_service import BillingService

        return BillingService.entitlement(user, "report")

    @staticmethod
    def get_transcript(user, meeting_id: int) -> tuple[dict, int]:
        meeting, err = SummaryService._check_access(user, meeting_id)
        if err:
            return err

        transcript = SummaryRepository.get_transcript(meeting_id)
        if not transcript:
            if meeting.status not in [MeetingStatus.COMPLETED]:
                return {
                    "message": "Transcription en cours de traitement.",
                    "status":  meeting.status,
                }, 202
            return {"error": "Transcription non disponible."}, 404

        return {"transcript": transcript.to_dict()}, 200

    @staticmethod
    def get_summary(user, meeting_id: int) -> tuple[dict, int]:
        meeting, err = SummaryService._check_access(user, meeting_id)
        if err:
            return err
        entitlement = SummaryService._check_report_access(user)
        if entitlement:
            return entitlement

        summary = SummaryRepository.get_summary(meeting_id)
        if not summary:
            if meeting.status not in [MeetingStatus.COMPLETED]:
                return {
                    "message": "Résumé en cours de génération.",
                    "status":  meeting.status,
                }, 202
            return {"error": "Résumé non disponible."}, 404

        return {"summary": summary.to_dict()}, 200

    @staticmethod
    def get_actions(user, meeting_id: int) -> tuple[dict, int]:
        _, err = SummaryService._check_access(user, meeting_id)
        if err:
            return err
        entitlement = SummaryService._check_report_access(user)
        if entitlement:
            return entitlement

        actions = SummaryRepository.get_actions(meeting_id)
        return {"actions": [a.to_dict() for a in actions]}, 200

    @staticmethod
    def get_decisions(user, meeting_id: int) -> tuple[dict, int]:
        _, err = SummaryService._check_access(user, meeting_id)
        if err:
            return err
        entitlement = SummaryService._check_report_access(user)
        if entitlement:
            return entitlement

        decisions = SummaryRepository.get_decisions(meeting_id)
        return {"decisions": [d.to_dict() for d in decisions]}, 200

    @staticmethod
    def get_questions(user, meeting_id: int) -> tuple[dict, int]:
        _, err = SummaryService._check_access(user, meeting_id)
        if err:
            return err
        entitlement = SummaryService._check_report_access(user)
        if entitlement:
            return entitlement

        questions = SummaryRepository.get_questions(meeting_id)
        return {"questions": [q.to_dict() for q in questions]}, 200

    @staticmethod
    def get_risks(user, meeting_id: int) -> tuple[dict, int]:
        _, err = SummaryService._check_access(user, meeting_id)
        if err:
            return err
        entitlement = SummaryService._check_report_access(user)
        if entitlement:
            return entitlement

        risks = SummaryRepository.get_risks(meeting_id)
        return {"risks": [r.to_dict() for r in risks]}, 200

    @staticmethod
    def get_full_report(user, meeting_id: int) -> tuple[dict, int]:
        """
        Retourne toutes les données IA en une seule réponse.
        Utilisé par l'onglet 'Compte rendu IA' du frontend.
        """
        meeting, err = SummaryService._check_access(user, meeting_id)
        if err:
            return err

        transcript = SummaryRepository.get_transcript(meeting_id)
        summary    = SummaryRepository.get_summary(meeting_id)
        decisions  = SummaryRepository.get_decisions(meeting_id)
        actions    = SummaryRepository.get_actions(meeting_id)
        questions  = SummaryRepository.get_questions(meeting_id)
        risks      = SummaryRepository.get_risks(meeting_id)

        entitlement = SummaryService._check_report_access(user)
        if entitlement:
            summary_text = summary.general_summary if summary else ""
            excerpt = (summary_text or "").strip()
            if len(excerpt) > 240:
                excerpt = f"{excerpt[:240].rstrip()}…"
            return {
                "meeting_id": meeting_id,
                "status": meeting.status,
                "locked": True,
                "payment_required": True,
                "code": "REPORT_PAYMENT_REQUIRED",
                "preview": {
                    "summary_excerpt": excerpt,
                    "decisions_count": len(decisions),
                    "actions_count": len(actions),
                    "questions_count": len(questions),
                    "risks_count": len(risks),
                },
            }, 200

        return {
            "meeting_id":  meeting_id,
            "status":      meeting.status,
            "locked":      False,
            "transcript":  transcript.to_dict() if transcript else None,
            "summary":     summary.to_dict()    if summary    else None,
            "decisions":   [d.to_dict() for d in decisions],
            "actions":     [a.to_dict() for a in actions],
            "questions":   [q.to_dict() for q in questions],
            "risks":       [r.to_dict() for r in risks],
        }, 200
