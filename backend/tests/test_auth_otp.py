from app import create_app
from config import Config
from services.email_service import EmailService


def make_test_app(tmp_path):
    class TestConfig(Config):
        TESTING = True
        DATABASE_URL = f"sqlite:///{tmp_path / 'otp-test.db'}"
        SQLALCHEMY_ECHO = False
        OTP_EXPIRY_MINUTES = 10
        OTP_RESEND_COOLDOWN_SECONDS = 60
        OTP_MAX_ATTEMPTS = 5

    return create_app(TestConfig)


def test_registration_requires_valid_otp_before_login(tmp_path, monkeypatch):
    sent = {}

    def fake_send(to_email, recipient_name, code):
        sent.update(email=to_email, name=recipient_name, code=code)
        return {"success": True}

    monkeypatch.setattr(EmailService, "send_verification_code", staticmethod(fake_send))
    client = make_test_app(tmp_path).test_client()
    credentials = {
        "name": "Marie Test",
        "email": "marie@example.com",
        "password": "MotDePasse123!",
    }

    registration = client.post("/api/auth/register", json=credentials)
    assert registration.status_code == 201
    assert registration.json["verification_required"] is True
    assert "access_token" not in registration.json
    assert sent["email"] == credentials["email"]
    assert len(sent["code"]) == 6

    login_before_verification = client.post(
        "/api/auth/login",
        json={"email": credentials["email"], "password": credentials["password"]},
    )
    assert login_before_verification.status_code == 403
    assert login_before_verification.json["code"] == "EMAIL_NOT_VERIFIED"

    wrong_code = client.post(
        "/api/auth/verify-email",
        json={"email": credentials["email"], "code": "000000"},
    )
    assert wrong_code.status_code == 400
    assert wrong_code.json["attempts_remaining"] == 4

    verification = client.post(
        "/api/auth/verify-email",
        json={"email": credentials["email"], "code": sent["code"]},
    )
    assert verification.status_code == 200
    assert verification.json["user"]["email_verified"] is True
    assert verification.json["access_token"]


def test_resend_is_rate_limited(tmp_path, monkeypatch):
    monkeypatch.setattr(
        EmailService,
        "send_verification_code",
        staticmethod(lambda *_args: {"success": True}),
    )
    client = make_test_app(tmp_path).test_client()
    client.post(
        "/api/auth/register",
        json={"name": "Test User", "email": "otp@example.com", "password": "password123"},
    )

    response = client.post(
        "/api/auth/resend-verification",
        json={"email": "otp@example.com"},
    )
    assert response.status_code == 429
    assert response.json["code"] == "OTP_COOLDOWN"
    assert 1 <= response.json["retry_after"] <= 60


def test_password_reset_uses_single_use_email_otp(tmp_path, monkeypatch):
    verification = {}
    reset = {}
    monkeypatch.setattr(
        EmailService,
        "send_verification_code",
        staticmethod(lambda *_args: verification.update(code=_args[-1]) or {"success": True}),
    )
    monkeypatch.setattr(
        EmailService,
        "send_password_reset_code",
        staticmethod(lambda *_args: reset.update(code=_args[-1]) or {"success": True}),
    )
    client = make_test_app(tmp_path).test_client()
    email = "reset@example.com"
    client.post("/api/auth/register", json={"name": "Reset User", "email": email, "password": "ancien123"})
    client.post("/api/auth/verify-email", json={"email": email, "code": verification["code"]})

    requested = client.post("/api/auth/forgot-password", json={"email": email})
    assert requested.status_code == 200
    assert len(reset["code"]) == 6

    changed = client.post("/api/auth/reset-password", json={
        "email": email, "code": reset["code"], "new_password": "nouveau123",
    })
    assert changed.status_code == 200
    assert client.post("/api/auth/login", json={"email": email, "password": "ancien123"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": email, "password": "nouveau123"}).status_code == 200
    assert client.post("/api/auth/reset-password", json={
        "email": email, "code": reset["code"], "new_password": "encore123",
    }).status_code == 400


def test_forgot_password_does_not_reveal_unknown_account(tmp_path):
    client = make_test_app(tmp_path).test_client()
    response = client.post("/api/auth/forgot-password", json={"email": "unknown@example.com"})
    assert response.status_code == 200
    assert "Si un compte" in response.json["message"]
