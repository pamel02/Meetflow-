"""
utils/logger.py - Configuration centralisée du logger Python
Tous les modules importent leur logger depuis ici ou via logging.getLogger(__name__).
"""

import logging
import logging.handlers
import os


def setup_logging(log_level: str = "INFO", log_file: str | None = "./logs/backend.log") -> None:
    """
    Configure le logger racine de l'application.
    À appeler une seule fois au démarrage dans app.py.

    Args:
        log_level: Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file:  Chemin vers le fichier de log rotatif.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Format des messages
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # ── Handler console ───────────────────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # ── Handler fichier rotatif (10 Mo × 5 fichiers max) ──────────────────
    file_handler = None
    if log_file:
        log_directory = os.path.dirname(os.path.abspath(log_file))
        os.makedirs(log_directory, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 Mo
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)

    # Supprime les handlers existants pour éviter les doublons
    if root_logger.handlers:
        root_logger.handlers.clear()

    root_logger.addHandler(console_handler)
    if file_handler:
        root_logger.addHandler(file_handler)

    # Réduit le niveau de verbosité des librairies tierces
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("faster_whisper").setLevel(logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logging.info(f"Logger initialisé – niveau={log_level}, fichier={log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Raccourci pour obtenir un logger nommé.
    Usage : logger = get_logger(__name__)
    """
    return logging.getLogger(name)
