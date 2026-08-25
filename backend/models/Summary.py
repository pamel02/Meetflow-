"""
models/Summary.py - Compte rendu structuré généré par le LLM
"""

from datetime import UTC, datetime

from database.database import db


class Summary(db.Model):
    __tablename__ = "summaries"

    id              = db.Column(db.Integer, primary_key=True)
    meeting_id      = db.Column(db.Integer, db.ForeignKey("meetings.id"), nullable=False, unique=True)
    general_summary = db.Column(db.Text, nullable=True)   # Résumé général
    participants    = db.Column(db.Text, nullable=True)   # JSON: liste des participants
    conclusion      = db.Column(db.Text, nullable=True)   # Conclusion
    pdf_path        = db.Column(db.String(300), nullable=True)  # Chemin vers le PDF généré
    created_at      = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at      = db.Column(db.DateTime, default=lambda: datetime.now(UTC),
                                onupdate=lambda: datetime.now(UTC))

    def to_dict(self) -> dict:
        import json
        
        # Désérialise participants
        participants = []
        if self.participants:
            try:
                participants = json.loads(self.participants)
            except (json.JSONDecodeError, TypeError):
                participants = []
        
        # Désérialise general_summary si c'est du JSON (sinon, texte brut)
        general_summary = self.general_summary
        if isinstance(general_summary, str):
            try:
                parsed = json.loads(general_summary)
                if isinstance(parsed, list):
                    general_summary = " ".join(parsed)
            except (json.JSONDecodeError, TypeError):
                pass  # Garde le texte brut
        
        # Désérialise conclusion si c'est du JSON (sinon, texte brut)
        conclusion = self.conclusion
        if isinstance(conclusion, str):
            try:
                parsed = json.loads(conclusion)
                if isinstance(parsed, list):
                    conclusion = " ".join(parsed)
            except (json.JSONDecodeError, TypeError):
                pass  # Garde le texte brut
        
        return {
            "id":              self.id,
            "meeting_id":      self.meeting_id,
            "general_summary": general_summary,
            "participants":    participants,
            "conclusion":      conclusion,
            "pdf_path":        self.pdf_path,
            "created_at":      self.created_at.isoformat() if self.created_at else None,
        }
