"""
ai/whisper_model.py - Interface avec Faster-Whisper pour la transcription audio
Charge le modèle une seule fois en mémoire (singleton).
"""

import logging
import os

logger = logging.getLogger(__name__)

# Instance singleton du modèle
_whisper_model = None


def get_whisper_model():
    """
    Retourne le modèle Faster-Whisper chargé (singleton).
    Le charge depuis le disque la première fois.
    """
    global _whisper_model

    if _whisper_model is not None:
        return _whisper_model

    try:
        from faster_whisper import WhisperModel

        model_size    = os.environ.get("WHISPER_MODEL_SIZE", "small")
        device        = os.environ.get("WHISPER_DEVICE", "cpu")
        compute_type  = os.environ.get("WHISPER_COMPUTE_TYPE", "int8")

        logger.info(f"Chargement du modèle Whisper '{model_size}' sur {device}...")
        _whisper_model = WhisperModel(model_size, device=device, compute_type=compute_type)
        logger.info("Modèle Whisper chargé avec succès.")

    except ImportError:
        logger.error("faster-whisper n'est pas installé. pip install faster-whisper")
        raise
    except Exception as e:
        logger.error(f"Erreur au chargement du modèle Whisper : {e}")
        raise

    return _whisper_model


def transcribe_file(audio_path: str, language: str = None) -> dict:
    """
    Transcrit un fichier audio.
    Retourne { text, language, segments } avec les horodatages.

    Args:
        audio_path: Chemin absolu vers le fichier audio.
        language:   Code langue (fr, en, None = auto-détection).
    """
    model = get_whisper_model()

    transcribe_options = {
        "beam_size":      5,
        "vad_filter":     True,        # Filtre les silences (Voice Activity Detection)
        "vad_parameters": {"min_silence_duration_ms": 500},
    }
    if language:
        transcribe_options["language"] = language

    logger.info(f"Transcription de : {audio_path}")
    segments_iter, info = model.transcribe(audio_path, **transcribe_options)

    full_text = ""
    segments  = []

    for seg in segments_iter:
        text = seg.text.strip()
        full_text += " " + text
        segments.append({
            "start": round(seg.start, 2),
            "end":   round(seg.end, 2),
            "text":  text,
        })

    return {
        "text":     full_text.strip(),
        "language": info.language,
        "segments": segments,
    }


def is_available() -> bool:
    """Vérifie si Faster-Whisper est installé et fonctionnel."""
    try:
        from faster_whisper import WhisperModel
        return True
    except ImportError:
        return False
