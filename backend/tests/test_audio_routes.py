"""Minimal security regression tests for audio routes."""

from app import create_app
from config import Config


class TestConfig(Config):
    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"
    LOG_FILE = None


def test_audio_playback_requires_authentication():
    app = create_app(TestConfig)
    client = app.test_client()

    response = client.get("/api/audio/file/1/segment_0000.webm")

    assert response.status_code == 401

