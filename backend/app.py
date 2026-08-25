"""
app.py - Point d'entrée principal de l'application Flask
Assistant IA de Réunion - Backend
"""

import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

# Charge les variables d'environnement depuis backend/.env en développement local.
backend_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(backend_env_path)

# Désactive la télémétrie ChromaDB/PostHog pour éviter les erreurs sur des versions
# incompatibles du package posthog dans l'environnement Python.
try:
    import posthog
    if hasattr(posthog, 'capture'):
        def _safe_posthog_capture(*args, **kwargs):
            return None
        posthog.capture = _safe_posthog_capture
    posthog.disabled = True
except Exception:
    pass

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

from api.audio_routes import audio_bp

# Import des blueprints (routes)
from api.auth_routes import auth_bp
from api.billing_routes import billing_bp
from api.chat_routes import chat_bp
from api.export_routes import export_bp
from api.health_routes import health_bp
from api.meeting_routes import meeting_bp
from api.organization_routes import organization_bp
from api.summary_routes import summary_bp
from config import Config, DevelopmentConfig, config_map
from database.database import init_db
from middleware.error_handler import register_error_handlers
from utils.logger import setup_logging


def create_app(config_class=None):
    """
    Factory function : crée et configure l'application Flask.
    Pattern recommandé pour les applications Flask modulaires.
    """
    if config_class is None:
        env_name = os.environ.get("FLASK_ENV", "default").lower()
        config_class = config_map.get(env_name, Config)

    app = Flask(__name__)
    app.config.from_object(config_class)
    config_class.validate()

    # --- Logging ---
    setup_logging(
        log_level=app.config.get("LOG_LEVEL", "INFO"),
        log_file=app.config.get("LOG_FILE", "./logs/backend.log")
    )

    # --- CORS ---
    # Autorise le frontend React (Vite) à communiquer avec le backend
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config["ALLOWED_ORIGINS"],
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })

    # --- Base de données ---
    with app.app_context():
        init_db(app)

    # --- Gestionnaires d'erreurs globaux ---
    register_error_handlers(app)

    # --- Logging des requêtes HTTP ---
    from middleware.logger import register_request_logging
    register_request_logging(app)

    # --- Enregistrement des blueprints ---
    app.register_blueprint(auth_bp,    url_prefix="/api/auth")
    app.register_blueprint(billing_bp, url_prefix="/api")
    app.register_blueprint(organization_bp, url_prefix="/api")
    app.register_blueprint(meeting_bp, url_prefix="/api")
    app.register_blueprint(audio_bp,   url_prefix="/api/audio")
    app.register_blueprint(summary_bp, url_prefix="/api")
    app.register_blueprint(chat_bp,    url_prefix="/api/chat")
    app.register_blueprint(export_bp,  url_prefix="/api/export")
    app.register_blueprint(health_bp,  url_prefix="/api")

    return app


# --- Lancement direct (développement) ---
if __name__ == "__main__":
    app = create_app(DevelopmentConfig)
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=app.config["DEBUG"]
    )
