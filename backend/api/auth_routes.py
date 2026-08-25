"""
api/auth_routes.py - Routes d'authentification
POST /api/auth/register
POST /api/auth/login
POST /api/auth/verify-email
POST /api/auth/resend-verification
POST /api/auth/logout
GET  /api/auth/me
POST /api/auth/refresh
PUT  /api/auth/profile
PUT  /api/auth/password
DELETE /api/auth/account
"""

from flask import Blueprint, jsonify, request

from middleware.jwt import jwt_required
from services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """Inscription d'un nouvel utilisateur."""
    data = request.get_json(silent=True) or {}
    response, status = AuthService.register(data)
    return jsonify(response), status


@auth_bp.route("/login", methods=["POST"])
def login():
    """Connexion : retourne un JWT valide 12h."""
    data = request.get_json(silent=True) or {}
    response, status = AuthService.login(data)
    return jsonify(response), status


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    response, status = AuthService.request_password_reset(request.get_json(silent=True) or {})
    return jsonify(response), status


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    response, status = AuthService.reset_password(request.get_json(silent=True) or {})
    return jsonify(response), status


@auth_bp.route("/verify-email", methods=["POST"])
def verify_email():
    """Valide le code OTP et ouvre la session du nouveau compte."""
    data = request.get_json(silent=True) or {}
    response, status = AuthService.verify_email(data)
    return jsonify(response), status


@auth_bp.route("/resend-verification", methods=["POST"])
def resend_verification():
    """Envoie un nouveau code OTP, avec limitation de fréquence."""
    data = request.get_json(silent=True) or {}
    response, status = AuthService.resend_verification(data)
    return jsonify(response), status


@auth_bp.route("/logout", methods=["POST"])
@jwt_required
def logout(current_user):
    """
    Déconnexion.
    Le frontend supprime simplement le JWT côté client.
    Le backend peut implémenter une blacklist ici si nécessaire.
    """
    return jsonify({"message": "Déconnexion réussie."}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required
def get_me(current_user):
    """Retourne les informations de l'utilisateur connecté."""
    response, status = AuthService.get_me(current_user)
    return jsonify(response), status


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required
def refresh(current_user):
    """Renouvelle le token JWT sans demander le mot de passe."""
    response, status = AuthService.refresh_token(current_user)
    return jsonify(response), status


@auth_bp.route("/profile", methods=["PUT"])
@jwt_required
def update_profile(current_user):
    """Met à jour le nom, l'email et/ou la préférence de langue."""
    data = request.get_json(silent=True) or {}
    response, status = AuthService.update_profile(current_user, data)
    return jsonify(response), status


@auth_bp.route("/password", methods=["PUT"])
@jwt_required
def update_password(current_user):
    """Change le mot de passe après vérification de l'ancien."""
    data = request.get_json(silent=True) or {}
    response, status = AuthService.update_password(current_user, data)
    return jsonify(response), status


@auth_bp.route("/account", methods=["DELETE"])
@jwt_required
def delete_account(current_user):
    """Supprime le compte et toutes ses données."""
    data = request.get_json(silent=True) or {}
    response, status = AuthService.delete_account(current_user, data)
    return jsonify(response), status
