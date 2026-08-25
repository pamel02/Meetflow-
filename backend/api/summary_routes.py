"""
api/summary_routes.py - Routes des données IA
GET /api/transcript/{meeting_id}
GET /api/summary/{meeting_id}
GET /api/actions/{meeting_id}
GET /api/decisions/{meeting_id}
GET /api/questions/{meeting_id}
GET /api/risks/{meeting_id}
GET /api/report/{meeting_id}     (toutes les données en une requête)
"""

from flask import Blueprint, jsonify

from middleware.jwt import jwt_required
from services.summary_service import SummaryService

summary_bp = Blueprint("summary", __name__)


@summary_bp.route("/transcript/<int:meeting_id>", methods=["GET"])
@jwt_required
def get_transcript(current_user, meeting_id: int):
    """Retourne la transcription complète d'une réunion."""
    response, status = SummaryService.get_transcript(current_user, meeting_id)
    return jsonify(response), status


@summary_bp.route("/summary/<int:meeting_id>", methods=["GET"])
@jwt_required
def get_summary(current_user, meeting_id: int):
    """Retourne le résumé structuré (résumé général, participants, conclusion)."""
    response, status = SummaryService.get_summary(current_user, meeting_id)
    return jsonify(response), status


@summary_bp.route("/actions/<int:meeting_id>", methods=["GET"])
@jwt_required
def get_actions(current_user, meeting_id: int):
    """Retourne la liste des actions identifiées avec leurs responsables."""
    response, status = SummaryService.get_actions(current_user, meeting_id)
    return jsonify(response), status


@summary_bp.route("/decisions/<int:meeting_id>", methods=["GET"])
@jwt_required
def get_decisions(current_user, meeting_id: int):
    """Retourne la liste des décisions prises pendant la réunion."""
    response, status = SummaryService.get_decisions(current_user, meeting_id)
    return jsonify(response), status


@summary_bp.route("/questions/<int:meeting_id>", methods=["GET"])
@jwt_required
def get_questions(current_user, meeting_id: int):
    """Retourne les questions restées sans réponse."""
    response, status = SummaryService.get_questions(current_user, meeting_id)
    return jsonify(response), status


@summary_bp.route("/risks/<int:meeting_id>", methods=["GET"])
@jwt_required
def get_risks(current_user, meeting_id: int):
    """Retourne les risques identifiés pendant la réunion."""
    response, status = SummaryService.get_risks(current_user, meeting_id)
    return jsonify(response), status


@summary_bp.route("/report/<int:meeting_id>", methods=["GET"])
@jwt_required
def get_full_report(current_user, meeting_id: int):
    """
    Retourne TOUTES les données IA en une seule requête.
    Utilisé par l'onglet 'Compte rendu IA' du frontend pour éviter
    plusieurs appels HTTP successifs.
    """
    response, status = SummaryService.get_full_report(current_user, meeting_id)
    return jsonify(response), status
