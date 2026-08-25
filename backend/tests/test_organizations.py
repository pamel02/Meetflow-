from app import create_app
from config import Config
from services.email_service import EmailService


def make_app(tmp_path):
    class TestConfig(Config):
        TESTING = True
        DATABASE_URL = f"sqlite:///{tmp_path / 'organizations.db'}"
        SQLALCHEMY_ECHO = False
        BILLING_ENFORCEMENT_ENABLED = False

    return create_app(TestConfig)


def register_and_verify(client, monkeypatch, email):
    sent = {}
    monkeypatch.setattr(EmailService, "send_verification_code", staticmethod(lambda _email, _name, code: sent.update(code=code) or {"success": True}))
    client.post("/api/auth/register", json={"name": email.split("@")[0], "email": email, "password": "password123"})
    response = client.post("/api/auth/verify-email", json={"email": email, "code": sent["code"]})
    return {"Authorization": f"Bearer {response.json['access_token']}"}


def test_organization_onboarding_and_tenant_isolation(tmp_path, monkeypatch):
    client = make_app(tmp_path).test_client()
    alpha_headers = register_and_verify(client, monkeypatch, "alpha@example.com")
    beta_headers = register_and_verify(client, monkeypatch, "beta@example.com")

    alpha_org = client.post("/api/organizations", headers=alpha_headers, json={"name": "Alpha SARL", "company_size": "1-10", "country": "Cameroun"})
    beta_org = client.post("/api/organizations", headers=beta_headers, json={"name": "Beta SARL", "company_size": "1-10", "country": "Cameroun"})
    assert alpha_org.status_code == 201
    assert beta_org.status_code == 201

    meeting = client.post("/api/meetings", headers=alpha_headers, json={"title": "Réunion Alpha"})
    assert meeting.status_code == 201
    meeting_id = meeting.json["meeting"]["id"]
    assert meeting.json["meeting"]["organization_id"] == alpha_org.json["organization"]["id"]

    assert client.get(f"/api/meetings/{meeting_id}", headers=alpha_headers).status_code == 200
    assert client.get(f"/api/meetings/{meeting_id}", headers=beta_headers).status_code == 404
    assert client.get("/api/meetings", headers=beta_headers).json["meetings"] == []


def test_only_admin_can_invite(tmp_path, monkeypatch):
    client = make_app(tmp_path).test_client()
    admin_headers = register_and_verify(client, monkeypatch, "admin@example.com")
    client.post("/api/organizations", headers=admin_headers, json={"name": "MeetFlow Team"})
    monkeypatch.setattr(EmailService, "send_organization_invitation", staticmethod(lambda *_args: {"success": True}))

    invitation = client.post("/api/organizations/invitations", headers=admin_headers, json={"email": "member@example.com", "role": "member"})
    assert invitation.status_code == 201
    assert invitation.json["email_sent"] is True

    member_headers = register_and_verify(client, monkeypatch, "member@example.com")
    profile = client.get("/api/auth/me", headers=member_headers)
    assert profile.json["user"]["organization"]["name"] == "MeetFlow Team"
    assert profile.json["user"]["organization_role"] == "member"

    forbidden = client.post("/api/organizations/invitations", headers=member_headers, json={"email": "other@example.com", "role": "member"})
    assert forbidden.status_code == 403
    assert client.post("/api/meetings", headers=member_headers, json={"title": "Interdit"}).status_code == 403
