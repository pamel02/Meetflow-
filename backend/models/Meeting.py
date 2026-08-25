"""
models/Meeting.py - Modèle réunion
Contient les métadonnées d'une réunion et son statut de traitement.
"""

from datetime import UTC, datetime

from database.database import db


class MeetingStatus:
    """Constantes pour les statuts d'une réunion."""
    PENDING       = "pending"        # En attente
    RECORDING     = "recording"      # Enregistrement en cours
    TRANSCRIBING  = "transcribing"   # Transcription
    ANALYZING     = "analyzing"      # Analyse IA
    COMPLETED     = "completed"      # Terminée
    ERROR         = "error"          # Erreur

    ALL = [PENDING, RECORDING, TRANSCRIBING, ANALYZING, COMPLETED, ERROR]


class Meeting(db.Model):
    __tablename__ = "meetings"

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=True, index=True)
    title        = db.Column(db.String(300), nullable=True)   # Peut être généré automatiquement
    description  = db.Column(db.Text, nullable=True)
    status       = db.Column(db.String(50), default=MeetingStatus.PENDING, index=True)
    duration     = db.Column(db.Integer, default=0)           # Durée en secondes
    segments_count = db.Column(db.Integer, default=0)         # Nombre de segments audio reçus
    processing_step    = db.Column(db.String(100), nullable=True)   # Étape actuelle de traitement
    processing_progress = db.Column(db.Integer, default=0)          # Progression 0-100
    error_message  = db.Column(db.Text, nullable=True)
    created_at   = db.Column(db.DateTime, default=lambda: datetime.now(UTC), index=True)
    updated_at   = db.Column(db.DateTime, default=lambda: datetime.now(UTC),
                             onupdate=lambda: datetime.now(UTC))
    ended_at     = db.Column(db.DateTime, nullable=True)      # Quand l'enregistrement s'est terminé

    # Relations
    audio_segments = db.relationship("AudioSegment", backref="meeting", lazy=True,
                                     cascade="all, delete-orphan")
    transcript     = db.relationship("Transcript",   backref="meeting", lazy=True,
                                     uselist=False, cascade="all, delete-orphan")
    summary        = db.relationship("Summary",      backref="meeting", lazy=True,
                                     uselist=False, cascade="all, delete-orphan")
    decisions      = db.relationship("Decision",     backref="meeting", lazy=True,
                                     cascade="all, delete-orphan")
    actions        = db.relationship("Action",       backref="meeting", lazy=True,
                                     cascade="all, delete-orphan")
    questions      = db.relationship("Question",     backref="meeting", lazy=True,
                                     cascade="all, delete-orphan")
    risks          = db.relationship("Risk",         backref="meeting", lazy=True,
                                     cascade="all, delete-orphan")

    def to_dict(self, include_relations=False) -> dict:
        data = {
            "id":                 self.id,
            "user_id":            self.user_id,
            "organization_id":    self.organization_id,
            "title":              self.title or "Sans titre",
            "description":        self.description,
            "status":             self.status,
            "duration":           self.duration,
            "segments_count":     self.segments_count,
            "processing_step":    self.processing_step,
            "processing_progress": self.processing_progress,
            "error_message":      self.error_message,
            "created_at":         self.created_at.isoformat() if self.created_at else None,
            "updated_at":         self.updated_at.isoformat() if self.updated_at else None,
            "ended_at":           self.ended_at.isoformat() if self.ended_at else None,
        }
        return data

    def __repr__(self):
        return f"<Meeting {self.id} [{self.status}]>"
