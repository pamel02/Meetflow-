"""
models/Risk.py - Risque identifié lors d'une réunion
"""

from datetime import UTC, datetime

from database.database import db


class Risk(db.Model):
    __tablename__ = "risks"

    id          = db.Column(db.Integer, primary_key=True)
    meeting_id  = db.Column(db.Integer, db.ForeignKey("meetings.id"), nullable=False, index=True)
    content     = db.Column(db.Text, nullable=False)
    severity    = db.Column(db.String(50), nullable=True)  # faible / moyen / élevé
    mitigation  = db.Column(db.Text, nullable=True)        # Mesure d'atténuation proposée
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

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
        
        severity = self.severity
        if isinstance(severity, str):
            try:
                parsed = json.loads(severity)
                if isinstance(parsed, list):
                    severity = " ".join(parsed)
            except (json.JSONDecodeError, TypeError):
                pass
        
        mitigation = self.mitigation
        if isinstance(mitigation, str):
            try:
                parsed = json.loads(mitigation)
                if isinstance(parsed, list):
                    mitigation = " ".join(parsed)
            except (json.JSONDecodeError, TypeError):
                pass
        
        return {
            "id":          self.id,
            "meeting_id":  self.meeting_id,
            "content":     content,
            "severity":    severity,
            "mitigation":  mitigation,
            "created_at":  self.created_at.isoformat() if self.created_at else None,
        }
