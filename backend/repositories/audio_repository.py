"""
repositories/audio_repository.py - Requêtes SQL liées aux segments audio
"""

from datetime import UTC, datetime

from database.database import db
from models.AudioSegment import AudioSegment, SegmentStatus


class AudioRepository:

    @staticmethod
    def find_by_meeting_and_number(
        meeting_id: int, segment_number: int
    ) -> AudioSegment | None:
        return AudioSegment.query.filter_by(
            meeting_id=meeting_id,
            segment_number=segment_number,
        ).first()

    @staticmethod
    def create(meeting_id: int, segment_number: int,
               filename: str, duration: float = 0.0,
               file_size: int = 0) -> AudioSegment:
        seg = AudioSegment(
            meeting_id=meeting_id,
            segment_number=segment_number,
            filename=filename,
            duration=duration,
            file_size=file_size,
            status=SegmentStatus.RECEIVED
        )
        db.session.add(seg)
        db.session.commit()
        return seg

    @staticmethod
    def find_by_meeting(meeting_id: int) -> list[AudioSegment]:
        return (AudioSegment.query
                .filter_by(meeting_id=meeting_id)
                .order_by(AudioSegment.segment_number.asc())
                .all())

    @staticmethod
    def find_pending(meeting_id: int) -> list[AudioSegment]:
        """Segments reçus mais pas encore transcrits."""
        return (AudioSegment.query
                .filter_by(meeting_id=meeting_id, status=SegmentStatus.RECEIVED)
                .order_by(AudioSegment.segment_number.asc())
                .all())

    @staticmethod
    def find_untranscribed(meeting_id: int) -> list[AudioSegment]:
        """Segments non encore transcrits (reçus OU en erreur récupérable)."""
        return (AudioSegment.query
                .filter(
                    AudioSegment.meeting_id == meeting_id,
                    AudioSegment.status.in_([SegmentStatus.RECEIVED, SegmentStatus.PROCESSING])
                )
                .order_by(AudioSegment.segment_number.asc())
                .all())

    @staticmethod
    def find_transcribed(meeting_id: int) -> list[AudioSegment]:
        """Segments déjà transcrits, triés par numéro."""
        return (AudioSegment.query
                .filter_by(meeting_id=meeting_id, status=SegmentStatus.TRANSCRIBED)
                .order_by(AudioSegment.segment_number.asc())
                .all())

    @staticmethod
    def all_transcribed(meeting_id: int) -> bool:
        """Vérifie que tous les segments reçus sont transcrits."""
        pending = (AudioSegment.query
                   .filter(
                       AudioSegment.meeting_id == meeting_id,
                       AudioSegment.status.in_([SegmentStatus.RECEIVED,
                                                SegmentStatus.PROCESSING])
                   ).count())
        return pending == 0

    @staticmethod
    def mark_processing(segment: AudioSegment) -> AudioSegment:
        segment.status = SegmentStatus.PROCESSING
        db.session.commit()
        return segment

    @staticmethod
    def mark_transcribed(segment: AudioSegment, text: str,
                          language: str = None) -> AudioSegment:
        """Sauvegarde le texte transcrit directement sur le segment."""
        segment.status           = SegmentStatus.TRANSCRIBED
        segment.transcript_text  = text
        segment.detected_language = language
        segment.transcribed_at   = datetime.now(UTC)
        db.session.commit()
        return segment

    @staticmethod
    def mark_error(segment: AudioSegment, error: str) -> AudioSegment:
        segment.status        = SegmentStatus.ERROR
        segment.error_message = error
        db.session.commit()
        return segment

    @staticmethod
    def update_status(segment: AudioSegment, status: str,
                      error: str = None) -> AudioSegment:
        segment.status = status
        if error:
            segment.error_message = error
        db.session.commit()
        return segment

    @staticmethod
    def count_by_meeting(meeting_id: int) -> int:
        return AudioSegment.query.filter_by(meeting_id=meeting_id).count()

    @staticmethod
    def get_last_segment_number(meeting_id: int) -> int:
        seg = (AudioSegment.query
               .filter_by(meeting_id=meeting_id)
               .order_by(AudioSegment.segment_number.desc())
               .first())
        return seg.segment_number if seg else 0
