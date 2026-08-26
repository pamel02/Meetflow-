"""Business rules for audio-segment ingestion and playback."""

import os

from flask import current_app
from werkzeug.utils import secure_filename

from models.Meeting import MeetingStatus
from repositories.audio_repository import AudioRepository
from repositories.meeting_repository import MeetingRepository
from utils.audio import get_audio_duration
from utils.file import ensure_meeting_upload_dir


class AudioService:
    """Coordinate audio persistence, authorization and background processing."""

    @staticmethod
    def upload_segment(user, data: dict, file) -> tuple[dict, int]:
        meeting_id = data.get("meeting_id")
        segment_number = data.get("segment_number")
        if not meeting_id or segment_number is None:
            return {"error": "meeting_id et segment_number sont requis."}, 400

        try:
            meeting_id = int(meeting_id)
            segment_number = int(segment_number)
        except (ValueError, TypeError):
            return {"error": "meeting_id et segment_number doivent être des entiers."}, 400

        if segment_number < 0:
            return {"error": "segment_number doit être positif ou nul."}, 400

        meeting = MeetingRepository.find_by_id_and_user(meeting_id, user.id)
        if not meeting:
            return {"error": "Réunion introuvable."}, 404
        if meeting.status not in (MeetingStatus.PENDING, MeetingStatus.RECORDING):
            return {"error": "Cette réunion n'accepte plus de nouveaux segments."}, 409

        # Upload retries are idempotent: one logical number produces one row.
        existing = AudioRepository.find_by_meeting_and_number(meeting_id, segment_number)
        if existing:
            return {
                "message": "Segment déjà reçu.",
                "segment": existing.to_dict(),
                "segments_count": meeting.segments_count,
            }, 200

        allowed = current_app.config["ALLOWED_AUDIO_EXTENSIONS"]
        original_name = secure_filename(file.filename or "segment.wav")
        extension = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else "wav"
        if extension not in allowed:
            return {
                "error": f"Format non supporté. Formats acceptés : {sorted(allowed)}"
            }, 400

        upload_dir = ensure_meeting_upload_dir(
            current_app.config["UPLOAD_FOLDER"], meeting_id
        )
        filename = (
            f"user_{user.id}_meeting_{meeting_id}_segment_{segment_number:04d}.{extension}"
        )
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)

        file_size = os.path.getsize(filepath)
        if file_size > current_app.config["MAX_AUDIO_SEGMENT_BYTES"]:
            os.remove(filepath)
            return {"error": "Segment audio trop volumineux."}, 413

        duration = get_audio_duration(filepath)
        from services.billing_service import BillingService

        entitlement = BillingService.entitlement(
            user, "audio", additional_seconds=duration
        )
        if entitlement:
            os.remove(filepath)
            return entitlement

        segment = AudioRepository.create(
            meeting_id=meeting_id,
            segment_number=segment_number,
            filename=filepath,
            duration=duration,
            file_size=file_size,
        )
        MeetingRepository.increment_segments(meeting)
        if meeting.status == MeetingStatus.PENDING:
            MeetingRepository.update_status(meeting, MeetingStatus.RECORDING)

        from workers.transcription_worker import transcribe_segment_now

        transcribe_segment_now(segment.id, current_app._get_current_object())
        return {
            "message": "Segment reçu. Transcription lancée.",
            "segment": segment.to_dict(),
            "segments_count": meeting.segments_count,
        }, 201

    @staticmethod
    def end_meeting(user, data: dict) -> tuple[dict, int]:
        meeting_id = data.get("meeting_id")
        if not meeting_id:
            return {"error": "meeting_id est requis."}, 400

        try:
            meeting_id = int(meeting_id)
        except (ValueError, TypeError):
            return {"error": "meeting_id doit être un entier."}, 400

        meeting = MeetingRepository.find_by_id_and_user(meeting_id, user.id)
        if not meeting:
            return {"error": "Réunion introuvable."}, 404
        if meeting.status not in (MeetingStatus.PENDING, MeetingStatus.RECORDING):
            return {"error": "Cette réunion est déjà terminée ou en traitement."}, 409

        segments_count = AudioRepository.count_by_meeting(meeting.id)
        if segments_count == 0:
            return {"error": "Aucun segment audio reçu pour cette réunion."}, 400

        MeetingRepository.mark_ended(meeting)
        from workers.transcription_worker import start_summary_pipeline

        start_summary_pipeline(meeting.id, current_app._get_current_object())
        return {
            "message": "Enregistrement terminé. Génération du bilan lancée.",
            "meeting_id": meeting.id,
            "segments_count": segments_count,
            "status": MeetingStatus.TRANSCRIBING,
        }, 200

    @staticmethod
    def get_audio_status(user, meeting_id: int) -> tuple[dict, int]:
        meeting = MeetingRepository.find_by_id_and_user(meeting_id, user.id)
        if not meeting:
            return {"error": "Réunion introuvable."}, 404

        segments = AudioRepository.find_by_meeting(meeting_id)
        transcribed = AudioRepository.find_transcribed(meeting_id)
        last_segment = segments[-1] if segments else None
        return {
            "meeting_id": meeting_id,
            "segments_count": len(segments),
            "transcribed_count": len(transcribed),
            "pending_count": len(segments) - len(transcribed),
            "segments": [segment.to_dict() for segment in segments],
            "last_segment_at": (
                last_segment.received_at.isoformat() if last_segment else None
            ),
            "status": meeting.status,
            "processing_step": meeting.processing_step,
            "processing_progress": meeting.processing_progress,
        }, 200

    @staticmethod
    def get_audio_file(user, meeting_id: int, filename: str) -> tuple[dict, int]:
        """Resolve a stored segment after ownership and path validation."""
        safe_filename = secure_filename(filename)
        if not safe_filename or safe_filename != filename:
            return {"error": "Nom de fichier invalide."}, 400

        meeting = MeetingRepository.find_by_id_and_user(meeting_id, user.id)
        if not meeting:
            return {"error": "Réunion introuvable."}, 404

        upload_root = os.path.realpath(current_app.config["UPLOAD_FOLDER"])
        file_path = os.path.realpath(
            os.path.join(upload_root, f"meeting_{meeting_id}", safe_filename)
        )
        if os.path.commonpath([upload_root, file_path]) != upload_root:
            return {"error": "Accès refusé."}, 403
        if not os.path.isfile(file_path):
            return {"error": "Fichier non trouvé."}, 404

        mime_types = {
            ".webm": "audio/webm",
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".m4a": "audio/mp4",
            ".ogg": "audio/ogg",
        }
        extension = os.path.splitext(safe_filename)[1].lower()
        return {
            "path": file_path,
            "mimetype": mime_types.get(extension, "application/octet-stream"),
        }, 200
