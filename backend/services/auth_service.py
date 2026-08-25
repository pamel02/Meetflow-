"""Logique métier de l'authentification et de la vérification email."""

import hashlib
import hmac
import secrets
from datetime import timedelta

from flask import current_app

from middleware.jwt import generate_token
from models.EmailVerification import EmailVerification, utc_now_naive
from models.PasswordReset import PasswordReset
from database.database import db
from repositories.email_verification_repository import EmailVerificationRepository
from repositories.user_repository import UserRepository
from schemas.auth_schema import validate_login, validate_register, validate_update_profile
from services.email_service import EmailService


class AuthService:
    @staticmethod
    def _hash_otp(user_id: int, code: str) -> str:
        secret = current_app.config["SECRET_KEY"].encode("utf-8")
        payload = f"{user_id}:{code}".encode("utf-8")
        return hmac.new(secret, payload, hashlib.sha256).hexdigest()

    @staticmethod
    def _issue_verification(user, enforce_cooldown: bool = True) -> tuple[dict, int]:
        now = utc_now_naive()
        verification = EmailVerificationRepository.find_by_user_id(user.id)

        if verification and verification.is_verified:
            return {"message": "Cette adresse email est déjà vérifiée."}, 200

        cooldown = current_app.config["OTP_RESEND_COOLDOWN_SECONDS"]
        if enforce_cooldown and verification and verification.sent_at:
            elapsed = int((now - verification.sent_at).total_seconds())
            if elapsed < cooldown:
                retry_after = cooldown - max(elapsed, 0)
                return {
                    "error": "Veuillez patienter avant de demander un nouveau code.",
                    "code": "OTP_COOLDOWN",
                    "retry_after": retry_after,
                }, 429

        code = f"{secrets.randbelow(1_000_000):06d}"
        expires_at = now + timedelta(minutes=current_app.config["OTP_EXPIRY_MINUTES"])

        if verification is None:
            verification = EmailVerification(user_id=user.id, code_hash="", expires_at=expires_at)

        verification.code_hash = AuthService._hash_otp(user.id, code)
        verification.expires_at = expires_at
        verification.sent_at = now
        verification.attempt_count = 0
        verification.verified_at = None
        EmailVerificationRepository.save(verification)

        delivery = EmailService.send_verification_code(user.email, user.name, code)
        if not delivery.get("success"):
            # Autoriser un nouvel essai immédiat lorsque le serveur email a échoué.
            verification.sent_at = now - timedelta(seconds=cooldown)
            EmailVerificationRepository.commit()
        response = {
            "message": (
                "Un code de vérification a été envoyé par email."
                if delivery.get("success")
                else "Le compte a été créé, mais l'email n'a pas pu être envoyé. Vous pouvez demander un nouveau code."
            ),
            "verification_required": True,
            "email_sent": bool(delivery.get("success")),
            "expires_in": current_app.config["OTP_EXPIRY_MINUTES"] * 60,
            "resend_after": cooldown if delivery.get("success") else 0,
        }
        return response, 200

    @staticmethod
    def register(data: dict) -> tuple[dict, int]:
        cleaned, errors = validate_register(data)
        if errors:
            return {"errors": errors}, 400

        if UserRepository.email_exists(cleaned["email"]):
            return {"error": "Cet email est déjà utilisé."}, 409

        user = UserRepository.create(
            name=cleaned["name"],
            email=cleaned["email"],
            password=cleaned["password"],
        )
        response, _ = AuthService._issue_verification(user, enforce_cooldown=False)
        response["user_id"] = user.id
        response["email"] = user.email
        return response, 201

    @staticmethod
    def verify_email(data: dict) -> tuple[dict, int]:
        email = (data.get("email") or "").strip().lower()
        code = str(data.get("code") or "").strip()
        if not email or len(code) != 6 or not code.isdigit():
            return {"error": "Saisissez le code à 6 chiffres reçu par email."}, 400

        user = UserRepository.find_by_email(email)
        verification = EmailVerificationRepository.find_by_user_id(user.id) if user else None
        if not user or not verification:
            return {"error": "Code invalide ou expiré."}, 400

        if verification.is_verified:
            token_data = generate_token(user.id)
            return {"message": "Adresse déjà vérifiée.", "user": user.to_dict(), **token_data}, 200

        now = utc_now_naive()
        if verification.expires_at <= now:
            return {"error": "Ce code a expiré. Demandez-en un nouveau.", "code": "OTP_EXPIRED"}, 400

        max_attempts = current_app.config["OTP_MAX_ATTEMPTS"]
        if verification.attempt_count >= max_attempts:
            return {"error": "Trop de tentatives. Demandez un nouveau code.", "code": "OTP_ATTEMPTS_EXCEEDED"}, 429

        expected_hash = AuthService._hash_otp(user.id, code)
        if not hmac.compare_digest(verification.code_hash, expected_hash):
            verification.attempt_count += 1
            EmailVerificationRepository.commit()
            remaining = max(max_attempts - verification.attempt_count, 0)
            return {
                "error": "Code incorrect.",
                "code": "OTP_INVALID",
                "attempts_remaining": remaining,
            }, 400

        verification.verified_at = now
        verification.code_hash = ""
        EmailVerificationRepository.commit()
        from services.organization_service import OrganizationService
        OrganizationService.accept_pending_invitations(user)
        token_data = generate_token(user.id)
        return {
            "message": "Votre adresse email est vérifiée.",
            "user": user.to_dict(),
            **token_data,
        }, 200

    @staticmethod
    def resend_verification(data: dict) -> tuple[dict, int]:
        email = (data.get("email") or "").strip().lower()
        if not email:
            return {"error": "L'adresse email est requise."}, 400

        user = UserRepository.find_by_email(email)
        if not user:
            # Réponse neutre pour ne pas révéler l'existence d'un compte.
            return {"message": "Si ce compte existe, un nouveau code sera envoyé."}, 200

        return AuthService._issue_verification(user, enforce_cooldown=True)

    @staticmethod
    def request_password_reset(data: dict) -> tuple[dict, int]:
        """Envoie un OTP sans révéler si l'adresse possède un compte."""
        email = (data.get("email") or "").strip().lower()
        if not email or "@" not in email:
            return {"error": "Saisissez une adresse email valide."}, 400

        neutral = {
            "message": "Si un compte correspond à cette adresse, un code de réinitialisation vient d'être envoyé.",
            "expires_in": current_app.config["OTP_EXPIRY_MINUTES"] * 60,
            "resend_after": current_app.config["OTP_RESEND_COOLDOWN_SECONDS"],
        }
        user = UserRepository.find_by_email(email)
        if not user:
            return neutral, 200

        now = utc_now_naive()
        reset = PasswordReset.query.filter_by(user_id=user.id).first()
        cooldown = current_app.config["OTP_RESEND_COOLDOWN_SECONDS"]
        if reset and reset.sent_at and (now - reset.sent_at).total_seconds() < cooldown:
            return neutral, 200

        code = f"{secrets.randbelow(1_000_000):06d}"
        expires_at = now + timedelta(minutes=current_app.config["OTP_EXPIRY_MINUTES"])
        if reset is None:
            reset = PasswordReset(user_id=user.id, code_hash="", expires_at=expires_at)
            db.session.add(reset)
        reset.code_hash = hmac.new(
            current_app.config["SECRET_KEY"].encode("utf-8"),
            f"password-reset:{user.id}:{code}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        reset.expires_at = expires_at
        reset.sent_at = now
        reset.attempt_count = 0
        reset.consumed_at = None
        db.session.commit()
        delivery = EmailService.send_password_reset_code(user.email, user.name, code)
        if not delivery.get("success"):
            reset.sent_at = now - timedelta(seconds=cooldown)
            db.session.commit()
        return neutral, 200

    @staticmethod
    def reset_password(data: dict) -> tuple[dict, int]:
        email = (data.get("email") or "").strip().lower()
        code = str(data.get("code") or "").strip()
        new_password = data.get("new_password") or ""
        if not email or len(code) != 6 or not code.isdigit():
            return {"error": "Saisissez le code à 6 chiffres reçu par email."}, 400
        if len(new_password) < 8:
            return {"error": "Le nouveau mot de passe doit contenir au moins 8 caractères."}, 400

        user = UserRepository.find_by_email(email)
        reset = PasswordReset.query.filter_by(user_id=user.id).first() if user else None
        invalid = {"error": "Code invalide ou expiré.", "code": "RESET_CODE_INVALID"}
        if not reset or reset.consumed_at is not None or reset.expires_at <= utc_now_naive():
            return invalid, 400
        max_attempts = current_app.config["OTP_MAX_ATTEMPTS"]
        if reset.attempt_count >= max_attempts:
            return {"error": "Trop de tentatives. Demandez un nouveau code.", "code": "RESET_ATTEMPTS_EXCEEDED"}, 429
        expected = hmac.new(
            current_app.config["SECRET_KEY"].encode("utf-8"),
            f"password-reset:{user.id}:{code}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(reset.code_hash, expected):
            reset.attempt_count += 1
            db.session.commit()
            return invalid, 400

        user.set_password(new_password)
        reset.code_hash = ""
        reset.consumed_at = utc_now_naive()
        db.session.commit()
        return {"message": "Votre mot de passe a été réinitialisé. Vous pouvez maintenant vous connecter."}, 200

    @staticmethod
    def login(data: dict) -> tuple[dict, int]:
        cleaned, errors = validate_login(data)
        if errors:
            return {"errors": errors}, 400

        user = UserRepository.find_by_email(cleaned["email"])
        if not user or not user.check_password(cleaned["password"]):
            return {"error": "Email ou mot de passe incorrect."}, 401

        verification = EmailVerificationRepository.find_by_user_id(user.id)
        if verification and not verification.is_verified:
            return {
                "error": "Votre adresse email doit être vérifiée avant la connexion.",
                "code": "EMAIL_NOT_VERIFIED",
                "verification_required": True,
                "email": user.email,
            }, 403

        from services.organization_service import OrganizationService
        OrganizationService.accept_pending_invitations(user)

        token_data = generate_token(user.id)
        return {"message": "Connexion réussie.", "user": user.to_dict(), **token_data}, 200

    @staticmethod
    def get_me(user) -> tuple[dict, int]:
        return {"user": user.to_dict()}, 200

    @staticmethod
    def refresh_token(user) -> tuple[dict, int]:
        token_data = generate_token(user.id)
        return {"message": "Token renouvelé.", **token_data}, 200

    @staticmethod
    def update_profile(user, data: dict) -> tuple[dict, int]:
        cleaned, errors = validate_update_profile(data)
        if errors:
            return {"errors": errors}, 400

        if "email" in cleaned:
            existing_user = UserRepository.find_by_email(cleaned["email"])
            if existing_user and existing_user.id != user.id:
                return {"error": "Cet email est déjà utilisé par un autre compte."}, 409

        user = UserRepository.update(user, **cleaned)
        return {"message": "Profil mis à jour.", "user": user.to_dict()}, 200

    @staticmethod
    def update_password(user, data: dict) -> tuple[dict, int]:
        old_password = data.get("old_password", "")
        new_password = data.get("new_password", "")
        if not user.check_password(old_password):
            return {"error": "Ancien mot de passe incorrect."}, 400
        if len(new_password) < 8:
            return {"error": "Le nouveau mot de passe doit contenir au moins 8 caractères."}, 400
        UserRepository.update_password(user, new_password)
        return {"message": "Mot de passe mis à jour."}, 200

    @staticmethod
    def delete_account(user, data: dict) -> tuple[dict, int]:
        password = data.get("password", "")
        if not user.check_password(password):
            return {"error": "Mot de passe incorrect."}, 400
        UserRepository.delete(user)
        return {"message": "Compte supprimé."}, 200
