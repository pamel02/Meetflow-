"""
middleware/jwt.py - Gestion des tokens JWT
Génération, validation et décoration des routes protégées.
"""

from datetime import UTC, datetime
from functools import wraps

import jwt
from flask import current_app, jsonify, request

from repositories.user_repository import UserRepository


def generate_token(user_id: int) -> dict:
    """
    Génère un JWT valide 12h.
    Retourne le token et sa date d'expiration.
    """
    now = datetime.now(UTC)
    expires_at = now + current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]

    payload = {
        "sub":  str(user_id),     # subject = identifiant utilisateur
        "iat":  now,               # issued at
        "exp":  expires_at,        # expiration
    }

    token = jwt.encode(
        payload,
        current_app.config["JWT_SECRET_KEY"],
        algorithm="HS256"
    )

    return {
        "access_token": token,
        "expires_at":   expires_at.isoformat(),
        "expires_in":   int(current_app.config["JWT_ACCESS_TOKEN_EXPIRES"].total_seconds())
    }


def decode_token(token: str) -> dict:
    """
    Décode et valide un token JWT.
    Lève une exception si invalide ou expiré.
    """
    return jwt.decode(
        token,
        current_app.config["JWT_SECRET_KEY"],
        algorithms=["HS256"]
    )


def jwt_required(f):
    """
    Décorateur pour protéger les routes.
    Vérifie la présence et la validité du JWT dans le header Authorization.
    Injecte l'utilisateur dans kwargs sous la clé 'current_user'.

    Usage :
        @jwt_required
        def ma_route(current_user):
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token manquant ou mal formé"}), 401

        token = auth_header.split(" ", 1)[1]

        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expiré, veuillez vous reconnecter"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token invalide"}), 401

        user_id = int(payload.get("sub", 0))
        user = UserRepository.find_by_id(user_id)

        if not user:
            return jsonify({"error": "Utilisateur introuvable"}), 401

        # En mode SaaS payant, seules l'authentification, la création de
        # l'entreprise et la facturation restent accessibles avant paiement.
        if current_app.config.get("BILLING_ENFORCEMENT_ENABLED", False):
            exempt_endpoints = {
                "organizations.create_organization",
                "organizations.current_organization",
            }
            endpoint = request.endpoint or ""
            is_exempt = (
                endpoint.startswith("auth.")
                or endpoint.startswith("billing.")
                or endpoint in exempt_endpoints
            )
            if not is_exempt:
                from services.billing_service import BillingService
                entitlement = BillingService.entitlement(user, "access")
                if entitlement:
                    payload, status = entitlement
                    return jsonify(payload), status

        # Injecte l'utilisateur dans la fonction de la route
        kwargs["current_user"] = user
        return f(*args, **kwargs)

    return decorated_function
