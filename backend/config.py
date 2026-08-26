"""
config.py - Configuration centralisée de l'application
Toutes les variables d'environnement sont lues ici.
"""

import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _path_setting(name: str, default: str) -> str:
    """Return an absolute path, resolving relative values from backend/."""
    value = os.environ.get(name, default)
    if os.path.isabs(value):
        return value
    return os.path.normpath(os.path.join(BASE_DIR, value))


class Config:
    """Configuration principale. Lit les variables depuis .env via python-dotenv."""

    IS_PRODUCTION = False

    # --- SMTP (email) ---
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com").strip()
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_EMAIL = os.getenv("SMTP_EMAIL", "").strip()
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip().replace(" ", "")
    OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", "10"))
    OTP_RESEND_COOLDOWN_SECONDS = int(os.getenv("OTP_RESEND_COOLDOWN_SECONDS", "60"))
    OTP_MAX_ATTEMPTS = int(os.getenv("OTP_MAX_ATTEMPTS", "5"))
    PUBLIC_APP_URL = os.getenv("PUBLIC_APP_URL", "http://localhost:5173").strip().rstrip("/")

    # --- Paiements Mobile Money (Riserva/Reeserva) ---
    RISERVA_BASE_URL = os.getenv("RISERVA_BASE_URL", "https://riserva.nalovan.cloud/api/v1").strip()
    RISERVA_API_KEY = os.getenv("RISERVA_API_KEY", "").strip()
    RISERVA_WEBHOOK_SECRET = os.getenv("RISERVA_WEBHOOK_SECRET", "").strip()
    RISERVA_MODE = os.getenv("RISERVA_MODE", "SANDBOX").strip().upper()
    RISERVA_TIMEOUT = int(os.getenv("RISERVA_TIMEOUT", "30"))
    PAYMENT_WEBHOOK_URL = os.getenv("PAYMENT_WEBHOOK_URL", "").strip()
    BILLING_ENFORCEMENT_ENABLED = os.getenv("BILLING_ENFORCEMENT_ENABLED", "false").lower() == "true"
    FREE_TRIAL_MINUTES = int(os.getenv("FREE_TRIAL_MINUTES", "10"))

    # --- Sécurité ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production-please")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)  # Session de 12h comme spécifié

    # --- Base de données ---
    # SQLite par défaut (portable, sans serveur)
    # Pour MySQL : "mysql+pymysql://user:pass@host/dbname"
    DATABASE_URL = os.environ.get(
        "DATABASE_URL",
        "sqlite:///./data/assistant_reunion.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Mettre True pour debugger les requêtes SQL

    # --- NVIDIA NIM (LLM distant compatible OpenAI) ---
    NVIDIA_BASE_URL = os.environ.get(
        "NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"
    )
    NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")
    NVIDIA_MODEL = os.environ.get(
        "NVIDIA_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b"
    )
    NVIDIA_TIMEOUT = int(os.environ.get("NVIDIA_TIMEOUT", "300"))
    NVIDIA_MAX_RETRIES = int(os.environ.get("NVIDIA_MAX_RETRIES", "2"))
    NVIDIA_MAX_TOKENS = int(os.environ.get("NVIDIA_MAX_TOKENS", "16384"))
    NVIDIA_TOP_P = float(os.environ.get("NVIDIA_TOP_P", "0.95"))
    NVIDIA_ENABLE_THINKING = os.environ.get("NVIDIA_ENABLE_THINKING", "true")
    NVIDIA_REASONING_BUDGET = int(os.environ.get("NVIDIA_REASONING_BUDGET", "16384"))

    # --- Ollama (embeddings locaux uniquement) ---
    OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "300"))  # secondes

    # --- Faster-Whisper (transcription) ---
    WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "small")
    WHISPER_DEVICE = os.environ.get("WHISPER_DEVICE", "cpu")
    WHISPER_COMPUTE_TYPE = os.environ.get("WHISPER_COMPUTE_TYPE", "int8")
    WHISPER_LANGUAGE = os.environ.get("WHISPER_LANGUAGE", None)  # None = auto-détection

    # --- ChromaDB (base vectorielle pour RAG) ---
    # _BASE résout les chemins relatifs depuis le dossier backend/,
    # indépendamment du répertoire courant au moment du lancement.
    CHROMA_PERSIST_DIR = _path_setting("CHROMA_PERSIST_DIR", "./data/chroma")
    CHROMA_COLLECTION_NAME = os.environ.get("CHROMA_COLLECTION_NAME", "reunions")

    # --- Fichiers ---
    UPLOAD_FOLDER = _path_setting("UPLOAD_FOLDER", "./uploads")
    EXPORT_FOLDER = _path_setting("EXPORT_FOLDER", "./exports")
    MAX_AUDIO_SEGMENT_BYTES = int(os.environ.get("MAX_AUDIO_SEGMENT_BYTES", 25 * 1024 * 1024))
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 Mo max par requête
    ALLOWED_AUDIO_EXTENSIONS = {"wav", "webm", "mp3", "ogg", "m4a"}

    # --- CORS ---
    ALLOWED_ORIGINS = os.environ.get(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:3000,http://localhost,http://127.0.0.1"
    ).split(",")
    ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS if origin.strip()]

    # --- Workers (tâches asynchrones) ---
    # On utilise des threads simples pour ne pas dépendre de Celery
    WORKER_MAX_THREADS = int(os.environ.get("WORKER_MAX_THREADS", "4"))

    # --- Logs ---
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE = _path_setting("LOG_FILE", "./logs/backend.log")

    @classmethod
    def validate(cls) -> None:
        """Fail fast when unsafe secrets are used in production."""
        if not cls.IS_PRODUCTION:
            return

        unsafe_values = {
            "SECRET_KEY": {"", "change-me-in-production-please"},
            "JWT_SECRET_KEY": {"", "jwt-secret-change-me"},
        }
        invalid = [
            name
            for name, forbidden in unsafe_values.items()
            if getattr(cls, name, "") in forbidden or len(getattr(cls, name, "")) < 32
        ]
        if invalid:
            raise RuntimeError(
                f"Configuration de production invalide : {', '.join(invalid)}"
            )
        if cls.BILLING_ENFORCEMENT_ENABLED and (not cls.RISERVA_API_KEY or not cls.RISERVA_WEBHOOK_SECRET):
            raise RuntimeError("RISERVA_API_KEY et RISERVA_WEBHOOK_SECRET sont requis quand la facturation est active.")


class DevelopmentConfig(Config):
    """Configuration développement : logs SQL activés, debug complet."""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Configuration production : pas de debug, logs minimaux."""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    IS_PRODUCTION = True


# Mapping pratique pour choisir la config via variable d'environnement
config_map = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "default":     Config
}
