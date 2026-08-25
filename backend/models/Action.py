"""
models/Action.py - Action à réaliser identifiée dans une réunion
"""

from datetime import UTC, datetime

from database.database import db


class Action(db.Model):
    __tablename__ = "actions"

    id           = db.Column(db.Integer, primary_key=True)
    meeting_id   = db.Column(db.Integer, db.ForeignKey("meetings.id"), nullable=False, index=True)
    content      = db.Column(db.Text, nullable=False)       # Description de l'action
    responsible  = db.Column(db.String(200), nullable=True) # Personne responsable
    deadline     = db.Column(db.String(100), nullable=True) # Échéance (texte libre)
    created_at   = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    def to_dict(self) -> dict:
        import json
        
        # Désérialise les champs s'ils sont en JSON
        content = self.content
        if isinstance(content, str):
            try:
                parsed = json.loads(content)
                if isinstance(parsed, list):
                    content = " ".join(parsed)
            except (json.JSONDecodeError, TypeError):
                pass
        
        responsible = self.responsible
        if isinstance(responsible, str):
            try:
                parsed = json.loads(responsible)
                if isinstance(parsed, list):
                    responsible = " ".join(parsed)
            except (json.JSONDecodeError, TypeError):
                pass
        
        deadline = self.deadline
        if isinstance(deadline, str):
            try:
                parsed = json.loads(deadline)
                if isinstance(parsed, list):
                    deadline = " ".join(parsed)
            except (json.JSONDecodeError, TypeError):
                pass
        
        return {
            "id":          self.id,
            "meeting_id":  self.meeting_id,
            "content":     content,
            "responsible": responsible,
            "deadline":    deadline,
            "created_at":  self.created_at.isoformat() if self.created_at else None,
        }
