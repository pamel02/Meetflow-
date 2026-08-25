"""Accès aux codes de vérification d'adresse email."""

from database.database import db
from models.EmailVerification import EmailVerification


class EmailVerificationRepository:
    @staticmethod
    def find_by_user_id(user_id: int) -> EmailVerification | None:
        return EmailVerification.query.filter_by(user_id=user_id).first()

    @staticmethod
    def save(verification: EmailVerification) -> EmailVerification:
        db.session.add(verification)
        db.session.commit()
        return verification

    @staticmethod
    def commit() -> None:
        db.session.commit()
