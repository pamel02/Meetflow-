"""Unit tests for request validation."""

from schemas.auth_schema import validate_register
from schemas.meeting_schema import validate_update_meeting


def test_register_normalizes_email():
    cleaned, errors = validate_register(
        {"name": "Alice", "email": " Alice@Example.COM ", "password": "password123"}
    )

    assert errors == []
    assert cleaned["email"] == "alice@example.com"


def test_register_rejects_short_password():
    _, errors = validate_register(
        {"name": "Alice", "email": "alice@example.com", "password": "short"}
    )

    assert any("8" in error for error in errors)


def test_meeting_title_has_a_maximum_length():
    _, errors = validate_update_meeting({"title": "x" * 301})

    assert errors

