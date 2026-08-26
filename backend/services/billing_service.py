"""Logique métier de facturation SaaS et validation des webhooks."""

import hashlib
import hmac
import json
import re
import time
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from flask import current_app
from sqlalchemy import func

from database.database import db
from integrations.riserva_client import RiservaClient, RiservaError
from models.AudioSegment import AudioSegment
from models.Billing import Payment, Plan, Subscription
from models.Meeting import Meeting
from models.Organization import Membership
from services.organization_service import OrganizationService


TERMINAL_STATUSES = {"COMPLETED", "FAILED", "REVERSED"}


def _utc_now():
    return datetime.now(UTC)


def _provider_value(payload, *keys, default=None):
    for key in keys:
        value = payload.get(key)
        if value is not None:
            return value
    return default


class BillingService:
    @staticmethod
    def plans():
        plans = Plan.query.filter_by(active=True).order_by(Plan.amount_xaf.asc()).all()
        return {"plans": [plan.to_dict() for plan in plans]}, 200

    @staticmethod
    def _membership(user, admin=False):
        membership = OrganizationService.membership_for(user)
        if not membership:
            return None, ({"error": "Configurez d'abord votre espace entreprise.", "code": "ONBOARDING_REQUIRED"}, 428)
        if admin and membership.role != "admin":
            return None, ({"error": "La facturation est réservée à l'administrateur de l'entreprise."}, 403)
        return membership, None

    @staticmethod
    def _active_subscription(organization_id):
        subscription = Subscription.query.filter_by(organization_id=organization_id).first()
        if subscription and subscription.status == "ACTIVE":
            end = subscription.current_period_end
            now = _utc_now()
            if end.tzinfo is None:
                now = now.replace(tzinfo=None)
            if end <= now:
                subscription.status = "PAST_DUE"
                db.session.commit()
        return subscription

    @staticmethod
    def _used_transcription_seconds(organization_id, subscription):
        """Compte uniquement les réunions réalisées depuis le dernier paiement."""
        if not subscription:
            return 0
        return db.session.query(func.coalesce(func.sum(Meeting.duration), 0)).filter(
            Meeting.organization_id == organization_id,
            Meeting.created_at >= subscription.current_period_start,
        ).scalar() or 0

    @classmethod
    def current(cls, user):
        membership, error = cls._membership(user)
        if error:
            return error
        subscription = cls._active_subscription(membership.organization_id)
        used_seconds = cls._used_transcription_seconds(membership.organization_id, subscription)
        if not subscription:
            used_seconds = db.session.query(
                func.coalesce(func.sum(AudioSegment.duration), 0)
            ).join(Meeting, Meeting.id == AudioSegment.meeting_id).filter(
                Meeting.organization_id == membership.organization_id
            ).scalar() or 0
        used_minutes = round(used_seconds / 60, 1)
        quota_minutes = (
            subscription.plan.transcription_minutes
            if subscription
            else current_app.config.get("FREE_TRIAL_MINUTES", 10)
        )
        usage = {
            "members": Membership.query.filter_by(organization_id=membership.organization_id).count(),
            "transcription_minutes": used_minutes,
            "transcription_minutes_remaining": max(round(quota_minutes - used_minutes, 1), 0),
            "transcription_quota_exhausted": bool(subscription and used_minutes >= quota_minutes),
            "trial_meeting_available": bool(
                not subscription and membership.organization.trial_started_at is None
            ),
            "trial_started": bool(
                not subscription and membership.organization.trial_started_at is not None
            ),
        }
        return {
            "subscription": subscription.to_dict() if subscription else None,
            "usage": usage,
            "provider_configured": RiservaClient.is_configured(),
            "provider_ready": RiservaClient.is_ready(),
            "provider_configuration_error": RiservaClient.configuration_error(),
            "mode": current_app.config.get("RISERVA_MODE", "SANDBOX").upper(),
            "enforcement_enabled": bool(current_app.config.get("BILLING_ENFORCEMENT_ENABLED", False)),
            "role": membership.role,
        }, 200

    @staticmethod
    def _normalize_phone(value):
        phone = re.sub(r"\D", "", str(value or ""))
        if phone.startswith("00"):
            phone = phone[2:]
        if len(phone) == 9 and phone.startswith("6"):
            phone = "237" + phone
        if not re.fullmatch(r"2376\d{8}", phone):
            raise ValueError("Saisissez un numéro camerounais valide, par exemple 2376XXXXXXXX.")
        return phone

    @staticmethod
    def _mask_phone(phone):
        return f"+{phone[:3]} ••• •• {phone[-4:]}"

    @classmethod
    def _checkout_data(cls, user, data):
        membership, error = cls._membership(user, admin=True)
        if error:
            return None, error
        plan = Plan.query.filter_by(code=(data.get("plan_code") or "").strip().lower(), active=True).first()
        if not plan:
            return None, ({"error": "Offre introuvable."}, 404)
        operator = (data.get("operator") or "").strip().lower()
        if operator not in {"mtn", "orange"}:
            return None, ({"error": "Choisissez MTN Mobile Money ou Orange Money."}, 400)
        try:
            phone = cls._normalize_phone(data.get("phone_number"))
        except ValueError as exc:
            return None, ({"error": str(exc)}, 400)
        return {"membership": membership, "plan": plan, "operator": operator, "phone": phone}, None

    @classmethod
    def quote(cls, user, data):
        values, error = cls._checkout_data(user, data)
        if error:
            return error
        payload = {
            "operator": values["operator"], "country": "CM",
            "amount": values["plan"].amount_xaf, "currency": "XAF", "type": "collect",
        }
        try:
            quote = RiservaClient.quote(payload)
        except RiservaError as exc:
            return {"error": str(exc), "code": exc.code}, exc.status
        return {"quote": quote, "plan": values["plan"].to_dict()}, 200

    @classmethod
    def checkout(cls, user, data):
        values, error = cls._checkout_data(user, data)
        if error:
            return error
        if not RiservaClient.is_configured():
            return {"error": "Ajoutez RISERVA_API_KEY dans backend/.env avant d'encaisser.", "code": "PAYMENT_NOT_CONFIGURED"}, 503
        if not RiservaClient.is_ready():
            return {"error": RiservaClient.configuration_error(), "code": "PAYMENT_MODE_MISMATCH"}, 503

        plan, membership = values["plan"], values["membership"]
        idempotency_key = f"meetflow-{uuid4()}"
        payment = Payment(
            organization_id=membership.organization_id,
            plan_id=plan.id,
            idempotency_key=idempotency_key,
            operator=values["operator"],
            phone_masked=cls._mask_phone(values["phone"]),
            amount=plan.amount_xaf,
            mode=current_app.config.get("RISERVA_MODE", "SANDBOX").upper(),
        )
        db.session.add(payment)
        db.session.commit()

        payload = {
            "operator": values["operator"], "country": "CM",
            "phone_number": values["phone"], "amount": plan.amount_xaf, "currency": "XAF",
        }
        webhook_url = current_app.config.get("PAYMENT_WEBHOOK_URL", "").strip()
        if webhook_url:
            payload["notify_url"] = webhook_url
        try:
            provider = RiservaClient.collect(payload, idempotency_key)
            cls._apply_provider_data(payment, provider)
            if payment.status == "COMPLETED":
                cls._activate(payment)
            db.session.commit()
        except RiservaError as exc:
            payment.status = "FAILED"
            payment.failure_reason = str(exc)[:500]
            db.session.commit()
            return {"error": str(exc), "code": exc.code, "payment": payment.to_dict()}, exc.status
        return {
            "message": "Demande envoyée. Confirmez le paiement sur votre téléphone.",
            "payment": payment.to_dict(),
        }, 201

    @staticmethod
    def _apply_provider_data(payment, provider):
        provider_id = _provider_value(provider, "id", "payment_id", "transaction_id", "transactionId")
        if provider_id:
            payment.provider_payment_id = str(provider_id)
        company_id = _provider_value(provider, "company_id", "companyId")
        if company_id:
            payment.provider_company_id = str(company_id)
        status = str(_provider_value(provider, "status", default="PENDING")).upper()
        if status in {"SUCCESS", "SUCCEEDED", "COLLECTED"}:
            status = "COMPLETED"
        if status in {"PENDING", "COMPLETED", "FAILED", "REVERSED"}:
            payment.status = status
        fee = _provider_value(provider, "fee", "fees")
        if fee is not None:
            payment.fee = str(fee)
        reason = _provider_value(provider, "failure_reason", "failureReason", "reason", "message")
        if payment.status == "FAILED" and reason:
            payment.failure_reason = str(reason)[:500]

    @classmethod
    def _activate(cls, payment):
        if payment.status == "COMPLETED" and payment.subscription_id:
            return
        now = _utc_now()
        subscription = Subscription.query.filter_by(organization_id=payment.organization_id).first()
        if subscription is None:
            subscription = Subscription(
                organization_id=payment.organization_id,
                plan_id=payment.plan_id,
                status="ACTIVE",
                current_period_start=now,
                current_period_end=now + timedelta(days=30),
            )
            db.session.add(subscription)
            db.session.flush()
        else:
            current_end = subscription.current_period_end
            comparison_now = now.replace(tzinfo=None) if current_end.tzinfo is None else now
            start = current_end if subscription.status == "ACTIVE" and current_end > comparison_now and subscription.plan_id == payment.plan_id else comparison_now
            subscription.plan_id = payment.plan_id
            subscription.status = "ACTIVE"
            subscription.current_period_start = comparison_now
            subscription.current_period_end = start + timedelta(days=30)
        payment.subscription_id = subscription.id
        payment.status = "COMPLETED"
        payment.completed_at = now

    @classmethod
    def payment(cls, user, payment_id):
        membership, error = cls._membership(user)
        if error:
            return error
        payment = Payment.query.filter_by(id=payment_id, organization_id=membership.organization_id).first()
        if not payment:
            return {"error": "Paiement introuvable."}, 404
        if payment.status == "PENDING" and payment.provider_payment_id:
            try:
                provider = RiservaClient.get_payment(payment.provider_payment_id)
                cls._apply_provider_data(payment, provider)
                if payment.status == "COMPLETED":
                    cls._activate(payment)
                db.session.commit()
            except RiservaError:
                pass
        return {"payment": payment.to_dict()}, 200

    @classmethod
    def payments(cls, user):
        membership, error = cls._membership(user)
        if error:
            return error
        rows = Payment.query.filter_by(organization_id=membership.organization_id).order_by(Payment.created_at.desc()).limit(50).all()
        return {"payments": [payment.to_dict() for payment in rows]}, 200

    @classmethod
    def webhook(cls, raw_body, headers):
        secret = current_app.config.get("RISERVA_WEBHOOK_SECRET", "").strip()
        if not secret:
            return {"error": "Webhook non configuré."}, 503
        signature = headers.get("X-Riserva-Signature", "")
        parts = dict(item.split("=", 1) for item in signature.split(",") if "=" in item)
        try:
            timestamp = int(parts["t"])
            supplied = parts["v1"]
        except (KeyError, ValueError):
            return {"error": "Signature de webhook invalide."}, 401
        if abs(int(time.time()) - timestamp) > 300:
            return {"error": "Webhook expiré."}, 401
        expected = hmac.new(secret.encode(), str(timestamp).encode() + b"." + raw_body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, supplied):
            return {"error": "Signature de webhook invalide."}, 401
        expected_mode = current_app.config.get("RISERVA_MODE", "SANDBOX").upper()
        received_mode = headers.get("X-Riserva-Mode")
        if received_mode and received_mode.upper() != expected_mode:
            return {"error": "Mode de webhook incohérent."}, 403
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {"error": "Corps de webhook invalide."}, 400

        event = headers.get("X-Riserva-Event") or payload.get("event") or payload.get("type", "")
        data = payload.get("data", payload)
        provider_id = _provider_value(data, "id", "payment_id", "transaction_id", "transactionId")
        payment = Payment.query.filter_by(provider_payment_id=str(provider_id)).first() if provider_id else None
        if not payment:
            return {"received": True, "ignored": True}, 200
        company = headers.get("X-Riserva-Company")
        if payment.provider_company_id and company and not hmac.compare_digest(payment.provider_company_id, company):
            return {"error": "Entreprise de paiement incohérente."}, 403

        if event in {"payment.collected", "payment.succeeded", "payment.completed"}:
            cls._apply_provider_data(payment, data)
            cls._activate(payment)
        elif event == "payment.failed":
            cls._apply_provider_data(payment, {**data, "status": "FAILED"})
        elif event == "payment.reversed":
            payment.status = "REVERSED"
        db.session.commit()
        return {"received": True}, 200

    @classmethod
    def entitlement(cls, user, kind, additional_seconds=0):
        """Autorise l'essai gratuit, puis protège les fonctions premium."""
        if not current_app.config.get("BILLING_ENFORCEMENT_ENABLED", False):
            return None
        membership = OrganizationService.membership_for(user)
        if not membership:
            return {
                "error": "Configurez d'abord votre espace entreprise.",
                "code": "ONBOARDING_REQUIRED",
            }, 428

        subscription = cls._active_subscription(membership.organization_id)
        if not subscription or subscription.status != "ACTIVE":
            if kind == "meeting":
                if membership.organization.trial_started_at is None:
                    return None
                return {
                    "error": "Votre réunion d'essai a déjà été utilisée. Choisissez une offre pour continuer.",
                    "code": "FREE_TRIAL_USED",
                    "payment_required": True,
                }, 402

            if kind == "audio":
                used_seconds = db.session.query(
                    func.coalesce(func.sum(AudioSegment.duration), 0)
                ).join(Meeting, Meeting.id == AudioSegment.meeting_id).filter(
                    Meeting.organization_id == membership.organization_id
                ).scalar() or 0
                limit_minutes = current_app.config.get("FREE_TRIAL_MINUTES", 10)
                if used_seconds + max(float(additional_seconds or 0), 0) <= limit_minutes * 60:
                    return None
                return {
                    "error": f"Les {limit_minutes} minutes de votre essai gratuit sont épuisées. Choisissez une offre pour continuer.",
                    "code": "FREE_TRIAL_LIMIT_REACHED",
                    "payment_required": True,
                    "trial_minutes": limit_minutes,
                }, 402

            code = "REPORT_PAYMENT_REQUIRED" if kind == "report" else "SUBSCRIPTION_REQUIRED"
            message = (
                "Votre compte rendu est prêt. Choisissez une offre pour le consulter et le recevoir par e-mail."
                if kind == "report"
                else "Un abonnement actif est nécessaire pour utiliser cette fonctionnalité."
            )
            return {"error": message, "code": code, "payment_required": True}, 402
        if kind == "member":
            count = Membership.query.filter_by(organization_id=membership.organization_id).count()
            if count >= subscription.plan.max_members:
                return {"error": "La limite de membres de votre offre est atteinte.", "code": "MEMBER_LIMIT_REACHED"}, 402
        if kind in {"meeting", "audio"}:
            seconds = cls._used_transcription_seconds(membership.organization_id, subscription)
            if kind == "audio":
                seconds = db.session.query(
                    func.coalesce(func.sum(AudioSegment.duration), 0)
                ).join(Meeting, Meeting.id == AudioSegment.meeting_id).filter(
                    Meeting.organization_id == membership.organization_id,
                    Meeting.created_at >= subscription.current_period_start,
                ).scalar() or 0
            quota_seconds = subscription.plan.transcription_minutes * 60
            quota_reached = (
                seconds >= quota_seconds
                if kind == "meeting"
                else seconds + max(float(additional_seconds or 0), 0) > quota_seconds
            )
            if quota_reached:
                return {
                    "error": "Votre pack de minutes est épuisé. Renouvelez une offre pour continuer à transcrire.",
                    "code": "TRANSCRIPTION_LIMIT_REACHED",
                    "renewal_required": True,
                }, 402
        return None

    @classmethod
    def start_trial(cls, user):
        """Mémorise l'essai au niveau entreprise afin qu'une suppression ne le réinitialise pas."""
        if not current_app.config.get("BILLING_ENFORCEMENT_ENABLED", False):
            return
        membership = OrganizationService.membership_for(user)
        if not membership or membership.organization.trial_started_at is not None:
            return
        subscription = cls._active_subscription(membership.organization_id)
        if subscription and subscription.status == "ACTIVE":
            return
        membership.organization.trial_started_at = _utc_now()
        db.session.commit()
