"""
api/export_routes.py - Routes d'export
GET /api/export/pdf/{meeting_id}
GET /api/export/json/{meeting_id}
"""

import os

from flask import Blueprint, jsonify, request, send_file

from config import Config
from middleware.jwt import jwt_required
from services.email_service import EmailService
from services.export_service import ExportService

export_bp = Blueprint("export", __name__)


@export_bp.route("/pdf/<int:meeting_id>", methods=["GET"])
@jwt_required
def export_pdf(current_user, meeting_id: int):
    """
    Génère et retourne le PDF du compte rendu.
    Le fichier est servi en téléchargement direct.
    """
    include_transcript = request.args.get("include_transcript", "false").lower() in {"1", "true", "yes"}
    result, status_code, _ = ExportService.export_pdf(current_user, meeting_id, include_transcript=include_transcript)

    if status_code != 200:
        return jsonify(result), status_code

    pdf_path = result

    if not os.path.exists(pdf_path):
        return jsonify({"error": "Fichier PDF introuvable."}), 404

    return send_file(
        pdf_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=(
            f"compte_rendu_reunion_{meeting_id}_avec_transcription.pdf"
            if include_transcript else f"compte_rendu_reunion_{meeting_id}.pdf"
        )
    )


@export_bp.route("/json/<int:meeting_id>", methods=["GET"])
@jwt_required
def export_json(current_user, meeting_id: int):
    """
    Retourne toutes les données de la réunion en JSON.
    Utile pour intégration avec d'autres outils.
    """
    response, status = ExportService.export_json(current_user, meeting_id)
    return jsonify(response), status


@export_bp.route("/send-report", methods=["POST"])
@jwt_required
def send_report(current_user):
    """
    Génère le PDF du meeting puis l'envoie aux adresses fournies via SMTP.
    Corps JSON attendu: { "meeting_id": int, "emails": ["a@b.com"] }
    """
    data = request.get_json(silent=True) or {}
    meeting_id = data.get("meeting_id")
    emails = data.get("emails")

    if not meeting_id or not emails:
        return jsonify({"error": "meeting_id et emails sont requis."}), 400

    # Génère le PDF (ou récupère le chemin existant)
    include_transcript = bool(data.get("include_transcript", False))
    result, status_code, _ = ExportService.export_pdf(
        current_user, int(meeting_id), include_transcript=include_transcript
    )
    if status_code != 200:
        return jsonify(result), status_code

    pdf_path = result
    if not os.path.exists(pdf_path):
        return jsonify({"error": "Fichier PDF introuvable."}), 404

    # Prépare l'email
    from_addr = f"Assistant IA <{Config.SMTP_EMAIL}>" if Config.SMTP_EMAIL else "Assistant IA"
    subject = data.get("subject") or f"Compte rendu réunion #{meeting_id}"
    html = data.get("html") or (
        f"<p>Bonjour,</p><p>Veuillez trouver ci-joint le compte rendu de la réunion #{meeting_id}.</p><p>Merci.</p>"
    )

    send_result = EmailService.send_report(from_addr, emails, subject, html, pdf_path)

    if not send_result.get("success"):
        status_code = 400
        return jsonify({"success": False, "message": "Impossible d'envoyer le rapport.", "detail": send_result}), status_code

    return jsonify({"success": True, "detail": send_result}), 200
