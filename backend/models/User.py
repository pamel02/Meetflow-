"""
models/User.py - Modèle utilisateur
Représente un compte dans la base de données.
"""

from datetime import UTC, datetime

from werkzeug.security import check_password_hash, generate_password_hash

from database.database import db


class User(db.Model):
    __tablename__ = "users"

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(120), nullable=False)
    email      = db.Column(db.String(200), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    language   = db.Column(db.String(10), default="fr")  # préférence de langue
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC),
                           onupdate=lambda: datetime.now(UTC))

    # Relation : un utilisateur possède plusieurs réunions
    meetings = db.relationship("Meeting", backref="owner", lazy=True,
                               cascade="all, delete-orphan")
    email_verification = db.relationship(
        "EmailVerification",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    memberships = db.relationship("Membership", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str):
        """Hash et stocke le mot de passe."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Vérifie le mot de passe fourni contre le hash stocké."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        """Sérialisation sécurisée (sans le hash du mot de passe)."""
        membership = self.memberships[0] if self.memberships else None
        return {
            "id":         self.id,
            "name":       self.name,
            "email":      self.email,
            "language":   self.language,
            # Les comptes historiques sans ligne de vérification restent valides.
            "email_verified": (
                self.email_verification is None or self.email_verification.is_verified
            ),
            "organization": membership.organization.to_dict() if membership else None,
            "organization_role": membership.role if membership else None,
            "onboarding_required": membership is None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<User {self.email}>"
