"""
utils/file.py - Utilitaires pour la gestion des fichiers
"""

import logging
import os
import shutil

logger = logging.getLogger(__name__)


def ensure_meeting_upload_dir(upload_root: str, meeting_id: int) -> str:
    """
    Crée et retourne le dossier dédié à une réunion.
    Structure : uploads/meeting_{id}/
    """
    dir_path = os.path.join(upload_root, f"meeting_{meeting_id}")
    os.makedirs(dir_path, exist_ok=True)
    return dir_path


def delete_meeting_files(meeting_id: int, upload_root: str = "./uploads") -> None:
    """
    Supprime le dossier audio d'une réunion et tous ses segments.
    Appelé lors de la suppression d'une réunion.
    """
    dir_path = os.path.join(upload_root, f"meeting_{meeting_id}")
    if os.path.exists(dir_path):
        try:
            shutil.rmtree(dir_path)
            logger.info(f"Dossier supprimé : {dir_path}")
        except Exception as e:
            logger.error(f"Impossible de supprimer {dir_path} : {e}")


def get_file_size_mb(filepath: str) -> float:
    """Retourne la taille d'un fichier en mégaoctets."""
    try:
        return os.path.getsize(filepath) / (1024 * 1024)
    except FileNotFoundError:
        return 0.0


def allowed_audio_file(filename: str,
                       allowed_extensions: set = None) -> bool:
    """Vérifie si l'extension du fichier est autorisée."""
    if allowed_extensions is None:
        allowed_extensions = {"wav", "webm", "mp3", "ogg", "m4a"}
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in allowed_extensions
