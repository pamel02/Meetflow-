"""Organisation SaaS, adhésions et invitations."""

from datetime import UTC, datetime
from database.database import db


def utc_now():
    return datetime.now(UTC)


class Organization(db.Model):
    __tablename__ = "organizations"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    sector = db.Column(db.String(100), nullable=True)
    company_size = db.Column(db.String(30), nullable=True)
    country = db.Column(db.String(80), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    memberships = db.relationship("Membership", back_populates="organization", cascade="all, delete-orphan")
    invitations = db.relationship("OrganizationInvitation", back_populates="organization", cascade="all, delete-orphan")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "sector": self.sector, "company_size": self.company_size, "country": self.country}


class Membership(db.Model):
    __tablename__ = "memberships"
    __table_args__ = (db.UniqueConstraint("organization_id", "user_id", name="uq_membership_org_user"),)
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = db.Column(db.String(30), nullable=False, default="member")
    joined_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    organization = db.relationship("Organization", back_populates="memberships")
    user = db.relationship("User", back_populates="memberships")

    def to_dict(self):
        return {"id": self.id, "role": self.role, "joined_at": self.joined_at.isoformat(), "user": {"id": self.user.id, "name": self.user.name, "email": self.user.email}}


class OrganizationInvitation(db.Model):
    __tablename__ = "organization_invitations"
    __table_args__ = (db.UniqueConstraint("organization_id", "email", name="uq_invitation_org_email"),)
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    email = db.Column(db.String(200), nullable=False, index=True)
    role = db.Column(db.String(30), nullable=False, default="member")
    invited_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    accepted_at = db.Column(db.DateTime, nullable=True)
    organization = db.relationship("Organization", back_populates="invitations")

    def to_dict(self):
        return {"id": self.id, "email": self.email, "role": self.role, "status": self.status, "created_at": self.created_at.isoformat()}
