"""
services/export_service.py - Génération des exports PDF et JSON
"""

import os

from flask import current_app

from repositories.audio_repository import AudioRepository
from repositories.meeting_repository import MeetingRepository
from repositories.summary_repository import SummaryRepository
from utils.pdf import generate_meeting_pdf


class ExportService:

    @staticmethod
    def export_pdf(user, meeting_id: int, include_transcript: bool = False) -> tuple[dict | str, int, dict | None]:
        """
        Génère ou retourne le PDF du compte rendu d'une réunion.
        Retourne (chemin_fichier, code, headers) ou (erreur_dict, code, None).
        """
        meeting = MeetingRepository.find_by_id_and_user(meeting_id, user.id)
        if not meeting:
            return {"error": "Réunion introuvable."}, 404, None

        from services.billing_service import BillingService

        entitlement = BillingService.entitlement(user, "report")
        if entitlement:
            payload, status = entitlement
            return payload, status, None

        summary   = SummaryRepository.get_summary(meeting_id)
        if not summary:
            return {"error": "Le compte rendu n'est pas encore disponible."}, 202, None

        # Récupère toutes les données pour le PDF
        transcript = SummaryRepository.get_transcript(meeting_id) if include_transcript else None
        decisions  = SummaryRepository.get_decisions(meeting_id)
        actions    = SummaryRepository.get_actions(meeting_id)
        questions  = SummaryRepository.get_questions(meeting_id)
        risks      = SummaryRepository.get_risks(meeting_id)

        export_dir = current_app.config["EXPORT_FOLDER"]
        os.makedirs(export_dir, exist_ok=True)

        # Nom de fichier incluant user id et meeting id pour traçabilité
        pdf_path = os.path.join(
            export_dir,
            f"user_{user.id}_meeting_{meeting_id}_report{'_with_transcript' if include_transcript else ''}.pdf"
        )

        # Génère le PDF
        generate_meeting_pdf(
            output_path=pdf_path,
            meeting=meeting,
            summary=summary,
            transcript=transcript,
            decisions=decisions,
            actions=actions,
            questions=questions,
            risks=risks
        )

        # Sauvegarde le chemin du PDF dans le résumé
        SummaryRepository.set_pdf_path(meeting_id, pdf_path)

        return pdf_path, 200, None

    @staticmethod
    def export_json(user, meeting_id: int) -> tuple[dict, int]:
        """
        Retourne toutes les données IA en JSON.
        Pratique pour intégration avec d'autres outils.
        """
        meeting = MeetingRepository.find_by_id_and_user(meeting_id, user.id)
        if not meeting:
            return {"error": "Réunion introuvable."}, 404

        from services.billing_service import BillingService

        entitlement = BillingService.entitlement(user, "report")
        if entitlement:
            return entitlement

        transcript = SummaryRepository.get_transcript(meeting_id)
        summary    = SummaryRepository.get_summary(meeting_id)
        decisions  = SummaryRepository.get_decisions(meeting_id)
        actions    = SummaryRepository.get_actions(meeting_id)
        questions  = SummaryRepository.get_questions(meeting_id)
        risks      = SummaryRepository.get_risks(meeting_id)
        segments   = AudioRepository.find_by_meeting(meeting_id)

        return {
            "meeting":    meeting.to_dict(),
            "transcript": transcript.to_dict() if transcript else None,
            "summary":    summary.to_dict()    if summary    else None,
            "decisions":  [d.to_dict() for d in decisions],
            "actions":    [a.to_dict() for a in actions],
            "questions":  [q.to_dict() for q in questions],
            "risks":      [r.to_dict() for r in risks],
            "segments":   [s.to_dict() for s in segments],
        }, 200
