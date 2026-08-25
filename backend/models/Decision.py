"""
models/Decision.py - Décision prise lors d'une réunion
"""

from datetime import UTC, datetime

from database.database import db


class Decision(db.Model):
    __tablename__ = "decisions"

    id          = db.Column(db.Integer, primary_key=True)
    meeting_id  = db.Column(db.Integer, db.ForeignKey("meetings.id"), nullable=False, index=True)
    content     = db.Column(db.Text, nullable=False)       # Texte de la décision
    context     = db.Column(db.Text, nullable=True)        # Contexte optionnel
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    def to_dict(self) -> dict:
        import json
        
        # Désérialise content et context s'ils sont en JSON
        content = self.content
        if isinstance(content, str):
            try:
                parsed = json.loads(content)
                if isinstance(parsed, list):
                    content = " ".join(parsed)
            except (json.JSONDecodeError, TypeError):
                pass
        
        context = self.context
        if isinstance(context, str):
            try:
                parsed = json.loads(context)
                if isinstance(parsed, list):
                    context = " ".join(parsed)
            except (json.JSONDecodeError, TypeError):
                pass
        
        return {
            "id":         self.id,
            "meeting_id": self.meeting_id,
            "content":    content,
            "context":    context,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
