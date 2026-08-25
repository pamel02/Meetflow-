"""
models/Transcript.py - Transcription complète d'une réunion
"""

from datetime import UTC, datetime

from database.database import db


class Transcript(db.Model):
    __tablename__ = "transcripts"

    id          = db.Column(db.Integer, primary_key=True)
    meeting_id  = db.Column(db.Integer, db.ForeignKey("meetings.id"), nullable=False, unique=True)
    full_text   = db.Column(db.Text, nullable=True)      # Texte complet fusionné
    language    = db.Column(db.String(20), nullable=True) # Langue détectée
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at  = db.Column(db.DateTime, default=lambda: datetime.now(UTC),
                            onupdate=lambda: datetime.now(UTC))

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "meeting_id": self.meeting_id,
            "full_text":  self.full_text,
            "language":   self.language,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
