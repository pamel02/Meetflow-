"""
utils/audio.py - Utilitaires audio
"""

import logging

logger = logging.getLogger(__name__)


def get_audio_duration(filepath: str) -> float:
    """
    Retourne la durée d'un fichier audio en secondes.
    Utilise mutagen si disponible, sinon retourne 60.0 (durée par défaut d'un segment).
    """
    try:
        from mutagen import File as MutagenFile
        audio = MutagenFile(filepath)
        if audio and audio.info:
            return audio.info.length
    except ImportError:
        logger.debug("mutagen non installé, durée par défaut utilisée.")
    except Exception as e:
        logger.warning(f"Impossible de lire la durée de {filepath} : {e}")

    # Durée par défaut : un segment dure 60s
    return 60.0


def format_duration(seconds: int) -> str:
    """
    Formate une durée en secondes vers HH:MM:SS.
    Exemple : 3725 → "1h02m05s"
    """
    if seconds <= 0:
        return "0s"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}h{m:02d}m{s:02d}s"
    if m > 0:
        return f"{m}m{s:02d}s"
    return f"{s}s"
