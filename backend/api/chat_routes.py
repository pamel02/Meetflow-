"""
api/chat_routes.py - Routes de l'assistant IA conversationnel
POST /api/chat                    (toutes les réunions)
POST /api/chat/{meeting_id}       (une réunion spécifique)
"""

from flask import Blueprint, jsonify, request

from middleware.jwt import jwt_required
from services.chat_service import ChatService

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("", methods=["POST"])
@jwt_required
def chat_global(current_user):
    """
    Répond à une question portant sur toutes les réunions de l'utilisateur.
    Corps JSON : { "question": str }
    """
    data = request.get_json(silent=True) or {}
    response, status = ChatService.chat_global(current_user, data)
    return jsonify(response), status


@chat_bp.route("/<int:meeting_id>", methods=["POST"])
@jwt_required
def chat_meeting(current_user, meeting_id: int):
    """
    Répond à une question portant sur une réunion spécifique.
    Corps JSON : { "question": str }
    """
    data = request.get_json(silent=True) or {}
    response, status = ChatService.chat_meeting(current_user, meeting_id, data)
    return jsonify(response), status
