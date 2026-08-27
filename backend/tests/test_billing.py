import hashlib
import hmac
import json
import time
from datetime import UTC, datetime, timedelta

from app import create_app
from config import Config
from database.database import db
from integrations.riserva_client import RiservaClient
from models.Billing import Plan, Subscription
from models.Meeting import Meeting
from models.Organization import Membership
from repositories.summary_repository import SummaryRepository
from services.email_service import EmailService


def make_app(tmp_path):
    class TestConfig(Config):
        TESTING = True
        DATABASE_URL = f"sqlite:///{tmp_path / 'billing.db'}"
        SQLALCHEMY_ECHO = False
        RISERVA_API_KEY = "rsk_test_example"
        RISERVA_WEBHOOK_SECRET = "whsec_test_example"
        RISERVA_MODE = "SANDBOX"

    return create_app(TestConfig)


def account(client, monkeypatch):
    sent = {}
    monkeypatch.setattr(EmailService, "send_verification_code", staticmethod(lambda *_args: sent.update(code=_args[-1]) or {"success": True}))
    client.post("/api/auth/register", json={"name": "Admin", "email": "admin@billing.cm", "password": "password123"})
    verified = client.post("/api/auth/verify-email", json={"email": "admin@billing.cm", "code": sent["code"]})
    headers = {"Authorization": f"Bearer {verified.json['access_token']}"}
    client.post("/api/organizations", headers=headers, json={"name": "Billing SARL", "country": "Cameroun"})
    return headers


def signed_headers(body, event="payment.collected", valid=True):
    timestamp = int(time.time())
    digest = hmac.new(b"whsec_test_example", str(timestamp).encode() + b"." + body, hashlib.sha256).hexdigest()
    if not valid:
        digest = "0" * 64
    return {
        "Content-Type": "application/json",
        "X-Riserva-Event": event,
        "X-Riserva-Signature": f"t={timestamp},v1={digest}",
        "X-Riserva-Mode": "SANDBOX",
    }


def test_checkout_and_signed_webhook_activate_subscription(tmp_path, monkeypatch):
    app = make_app(tmp_path)
    client = app.test_client()
    headers = account(client, monkeypatch)
    monkeypatch.setattr(RiservaClient, "collect", classmethod(lambda cls, payload, key: {
        "id": "pay_provider_1", "status": "PENDING", "company_id": "company_1", "fee": 25,
    }))

    checkout = client.post("/api/billing/checkout", headers=headers, json={
        "plan_code": "business", "operator": "mtn", "phone_number": "670000002",
    })
    assert checkout.status_code == 201
    assert checkout.json["payment"]["status"] == "PENDING"
    assert checkout.json["payment"]["phone"].endswith("0002")
    assert client.get("/api/billing/subscription", headers=headers).json["subscription"] is None

    body = json.dumps({"data": {"id": "pay_provider_1", "status": "COMPLETED"}}, separators=(",", ":")).encode()
    webhook_headers = signed_headers(body)
    webhook_headers["X-Riserva-Company"] = "company_1"
    assert client.post("/api/webhooks/riserva", data=body, headers=webhook_headers).status_code == 200
    # Un même événement peut être livré plusieurs fois sans prolonger deux fois la période.
    first = client.get("/api/billing/subscription", headers=headers).json["subscription"]
    assert client.post("/api/webhooks/riserva", data=body, headers=webhook_headers).status_code == 200
    second = client.get("/api/billing/subscription", headers=headers).json["subscription"]
    assert first["plan"]["code"] == "business"
    assert first["current_period_end"] == second["current_period_end"]


def test_webhook_rejects_invalid_signature(tmp_path):
    client = make_app(tmp_path).test_client()
    body = b'{"data":{"id":"unknown"}}'
    response = client.post("/api/webhooks/riserva", data=body, headers=signed_headers(body, valid=False))
    assert response.status_code == 401


def test_public_plan_catalog_uses_requested_prices(tmp_path):
    client = make_app(tmp_path).test_client()
    response = client.get("/api/billing/plans")
    assert response.status_code == 200
    assert [(plan["code"], plan["amount_xaf"]) for plan in response.json["plans"]] == [
        ("starter", 1000), ("business", 1500), ("enterprise", 2000),
    ]
    assert [(plan["code"], plan["transcription_minutes"]) for plan in response.json["plans"]] == [
        ("starter", 120), ("business", 250), ("enterprise", 400),
    ]


def test_exhausted_minutes_require_a_new_payment_cycle(tmp_path, monkeypatch):
    app = make_app(tmp_path)
    app.config["BILLING_ENFORCEMENT_ENABLED"] = True
    client = app.test_client()
    headers = account(client, monkeypatch)

    with app.app_context():
        membership = Membership.query.first()
        plan = Plan.query.filter_by(code="starter").first()
        now = datetime.now(UTC)
        subscription = Subscription(
            organization_id=membership.organization_id,
            plan_id=plan.id,
            status="ACTIVE",
            current_period_start=now - timedelta(days=1),
            current_period_end=now + timedelta(days=29),
        )
        db.session.add(subscription)
        db.session.add(Meeting(
            user_id=membership.user_id,
            organization_id=membership.organization_id,
            duration=120 * 60,
            created_at=now,
        ))
        db.session.commit()

    usage = client.get("/api/billing/subscription", headers=headers).json["usage"]
    assert usage["transcription_quota_exhausted"] is True
    assert usage["transcription_minutes_remaining"] == 0
    blocked = client.post("/api/meetings", headers=headers, json={"title": "Réunion bloquée"})
    assert blocked.status_code == 402
    assert blocked.json["code"] == "TRANSCRIPTION_LIMIT_REACHED"
    assert blocked.json["renewal_required"] is True

    # Un paiement confirmé ouvre un nouveau cycle et remet le compteur à zéro.
    with app.app_context():
        subscription = Subscription.query.first()
        subscription.current_period_start = datetime.now(UTC) + timedelta(seconds=1)
        db.session.commit()

    renewed = client.get("/api/billing/subscription", headers=headers).json["usage"]
    assert renewed["transcription_minutes"] == 0
    assert renewed["transcription_quota_exhausted"] is False


def test_first_ten_minute_report_is_free_then_payment_is_required(tmp_path, monkeypatch):
    app = make_app(tmp_path)
    app.config["BILLING_ENFORCEMENT_ENABLED"] = True
    client = app.test_client()
    headers = account(client, monkeypatch)

    assert client.get("/api/meetings", headers=headers).status_code == 200

    created = client.post("/api/meetings", headers=headers, json={"title": "Réunion d'essai"})
    assert created.status_code == 201
    meeting_id = created.json["meeting"]["id"]

    second = client.post("/api/meetings", headers=headers, json={"title": "Deuxième réunion"})
    assert second.status_code == 402
    assert second.json["code"] == "FREE_TRIAL_USED"

    with app.app_context():
        meeting = db.session.get(Meeting, meeting_id)
        meeting.status = "completed"
        SummaryRepository.save_summary(
            meeting_id,
            "Le lancement est validé et trois actions prioritaires ont été retenues.",
            ["Alice", "Bob"],
            "Prochaine revue vendredi.",
        )
        SummaryRepository.save_actions(meeting_id, [{"content": "Préparer le lancement"}])

    report = client.get(f"/api/report/{meeting_id}", headers=headers)
    assert report.status_code == 200
    assert report.json["locked"] is False
    assert report.json["summary"]["general_summary"].startswith("Le lancement")
    assert "summary" in client.get(f"/api/meetings/{meeting_id}", headers=headers).json["meeting"]
    assert client.get(f"/api/summary/{meeting_id}", headers=headers).status_code == 200
    assert client.get(f"/api/export/json/{meeting_id}", headers=headers).status_code == 200

    with app.app_context():
        membership = Membership.query.first()
        second_meeting = Meeting(
            user_id=membership.user_id,
            organization_id=membership.organization_id,
            title="Deuxième rapport",
            status="completed",
            duration=60,
        )
        db.session.add(second_meeting)
        db.session.commit()
        second_meeting_id = second_meeting.id
        SummaryRepository.save_summary(
            second_meeting_id,
            "Ce second rapport nécessite un paiement.",
            [],
            "Fin.",
        )

    locked_report = client.get(f"/api/report/{second_meeting_id}", headers=headers)
    assert locked_report.status_code == 200
    assert locked_report.json["locked"] is True
    blocked_export = client.get(f"/api/export/json/{second_meeting_id}", headers=headers)
    assert blocked_export.status_code == 402
    assert blocked_export.json["code"] == "REPORT_PAYMENT_REQUIRED"

    assert client.delete(f"/api/meetings/{meeting_id}", headers=headers).status_code == 200
    after_delete = client.post("/api/meetings", headers=headers, json={"title": "Nouvel essai"})
    assert after_delete.status_code == 402
    assert after_delete.json["code"] == "FREE_TRIAL_USED"

    assert client.get("/api/billing/subscription", headers=headers).status_code == 200
    assert client.get("/api/billing/plans").status_code == 200
