"""
utils/timer.py - Utilitaire de mesure du temps d'exécution
Pratique pour monitorer les étapes lentes du pipeline (Whisper, NVIDIA NIM).
"""

import logging
import time
from contextlib import contextmanager
from functools import wraps

logger = logging.getLogger(__name__)


@contextmanager
def timer(label: str = "Opération"):
    """
    Context manager pour mesurer la durée d'un bloc de code.

    Usage :
        with timer("Transcription Whisper"):
            result = transcribe_file(path)
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        logger.info(f"⏱ {label} : {elapsed:.2f}s")


def timed(label: str = None):
    """
    Décorateur pour mesurer la durée d'une fonction.

    Usage :
        @timed("Génération du résumé")
        def generate_summary(text):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = label or func.__name__
            start = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            logger.info(f"⏱ {name} : {elapsed:.2f}s")
            return result
        return wrapper
    return decorator


def format_elapsed(seconds: float) -> str:
    """Formate une durée en secondes de manière lisible."""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs    = int(seconds % 60)
    return f"{minutes}m{secs:02d}s"
