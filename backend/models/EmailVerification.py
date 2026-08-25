"""Code de vérification associé à un nouveau compte utilisateur."""

from datetime import UTC, datetime

from database.database import db


def utc_now_naive():
    """SQLite restitue les DateTime sans fuseau : garder une base UTC comparable."""
    return datetime.now(UTC).replace(tzinfo=None)


class EmailVerification(db.Model):
    __tablename__ = "email_verifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    code_hash = db.Column(db.String(64), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    sent_at = db.Column(db.DateTime, nullable=False, default=utc_now_naive)
    attempt_count = db.Column(db.Integer, nullable=False, default=0)
    verified_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now_naive)
    updated_at = db.Column(db.DateTime, nullable=False, default=utc_now_naive, onupdate=utc_now_naive)

    user = db.relationship("User", back_populates="email_verification")

    @property
    def is_verified(self) -> bool:
        return self.verified_at is not None
