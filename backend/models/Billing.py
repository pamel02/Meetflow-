"""Plans, abonnements d'entreprise et paiements Mobile Money."""

from datetime import UTC, datetime
from uuid import uuid4

from database.database import db


def utc_now():
    return datetime.now(UTC)


class Plan(db.Model):
    __tablename__ = "plans"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False, index=True)
    name = db.Column(db.String(80), nullable=False)
    amount_xaf = db.Column(db.Integer, nullable=False)
    max_members = db.Column(db.Integer, nullable=False)
    transcription_minutes = db.Column(db.Integer, nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "amount_xaf": self.amount_xaf,
            "currency": "XAF",
            "max_members": self.max_members,
            "transcription_minutes": self.transcription_minutes,
            "active": self.active,
        }


class Subscription(db.Model):
    __tablename__ = "subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("plans.id"), nullable=False)
    status = db.Column(db.String(24), nullable=False, default="ACTIVE")
    current_period_start = db.Column(db.DateTime, nullable=False)
    current_period_end = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    updated_at = db.Column(db.DateTime, nullable=False, default=utc_now, onupdate=utc_now)
    plan = db.relationship("Plan")

    def to_dict(self):
        return {
            "id": self.id,
            "status": self.status,
            "current_period_start": self.current_period_start.isoformat(),
            "current_period_end": self.current_period_end.isoformat(),
            "plan": self.plan.to_dict(),
        }


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("plans.id"), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey("subscriptions.id"), nullable=True)
    provider_payment_id = db.Column(db.String(120), unique=True, nullable=True, index=True)
    provider_company_id = db.Column(db.String(120), nullable=True)
    idempotency_key = db.Column(db.String(80), unique=True, nullable=False)
    status = db.Column(db.String(24), nullable=False, default="PENDING", index=True)
    operator = db.Column(db.String(16), nullable=False)
    phone_masked = db.Column(db.String(24), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    fee = db.Column(db.String(32), nullable=True)
    currency = db.Column(db.String(8), nullable=False, default="XAF")
    mode = db.Column(db.String(16), nullable=False, default="SANDBOX")
    failure_reason = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    completed_at = db.Column(db.DateTime, nullable=True)
    plan = db.relationship("Plan")
    subscription = db.relationship("Subscription")

    def to_dict(self):
        return {
            "id": self.id,
            "provider_payment_id": self.provider_payment_id,
            "status": self.status,
            "operator": self.operator,
            "phone": self.phone_masked,
            "amount": self.amount,
            "fee": self.fee,
            "currency": self.currency,
            "mode": self.mode,
            "failure_reason": self.failure_reason,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "plan": self.plan.to_dict(),
        }
