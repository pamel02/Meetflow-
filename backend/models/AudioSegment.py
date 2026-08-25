"""
models/AudioSegment.py - Modèle segment audio
Représente un fichier audio de 60s envoyé par le frontend.
La transcription de chaque segment est conservée ici (transcript_text).
"""

from datetime import UTC, datetime

from database.database import db


class SegmentStatus:
    RECEIVED    = "received"     # Reçu, en attente de transcription
    PROCESSING  = "processing"   # Whisper en cours sur ce segment
    TRANSCRIBED = "transcribed"  # Transcription terminée et stockée
    ERROR       = "error"        # Échec de la transcription


class AudioSegment(db.Model):
    __tablename__ = "audio_segments"
    __table_args__ = (
        db.UniqueConstraint(
            "meeting_id", "segment_number", name="uq_audio_segment_meeting_number"
        ),
    )

    id                = db.Column(db.Integer, primary_key=True)
    meeting_id        = db.Column(db.Integer, db.ForeignKey("meetings.id"),
                                  nullable=False, index=True)
    segment_number    = db.Column(db.Integer, nullable=False)      # Numéro d'ordre (0-based)
    filename          = db.Column(db.String(300), nullable=False)   # Chemin absolu sur disque
    duration          = db.Column(db.Float, default=0.0)            # Durée en secondes
    file_size         = db.Column(db.Integer, default=0)            # Taille en octets
    status            = db.Column(db.String(50),
                                  default=SegmentStatus.RECEIVED, index=True)

    # Transcription stockée sur le segment (conservée définitivement)
    transcript_text   = db.Column(db.Text, nullable=True)
    detected_language = db.Column(db.String(10), nullable=True)

    error_message     = db.Column(db.Text, nullable=True)
    received_at       = db.Column(db.DateTime,
                                  default=lambda: datetime.now(UTC))
    transcribed_at    = db.Column(db.DateTime, nullable=True)       # Fin de transcription

    def to_dict(self) -> dict:
        return {
            "id":               self.id,
            "meeting_id":       self.meeting_id,
            "segment_number":   self.segment_number,
            "filename":         self.filename,
            "duration":         self.duration,
            "file_size":        self.file_size,
            "status":           self.status,
            "has_transcript":   bool(self.transcript_text),
            "detected_language": self.detected_language,
            "error_message":    self.error_message,
            "received_at":      self.received_at.isoformat() if self.received_at else None,
            "transcribed_at":   self.transcribed_at.isoformat() if self.transcribed_at else None,
        }

    def __repr__(self):
        return f"<AudioSegment meeting={self.meeting_id} seg={self.segment_number} [{self.status}]>"
