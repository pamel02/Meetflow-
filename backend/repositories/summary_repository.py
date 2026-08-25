"""
repositories/summary_repository.py - Requêtes SQL pour les données IA
(résumés, décisions, actions, questions, risques, transcriptions)
"""

import json

from database.database import db
from models.Action import Action
from models.Decision import Decision
from models.Question import Question
from models.Risk import Risk
from models.Summary import Summary
from models.Transcript import Transcript


def _normalize_text(value):
    """Convertit les listes en JSON, garde les strings, retourne '' pour None."""
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False)
    return value or ""


class SummaryRepository:

    # ── Transcription ──────────────────────────────────────────────

    @staticmethod
    def save_transcript(meeting_id: int, full_text: str,
                        language: str = None) -> Transcript:
        existing = Transcript.query.filter_by(meeting_id=meeting_id).first()
        if existing:
            existing.full_text = full_text
            existing.language  = language
            db.session.commit()
            return existing
        t = Transcript(meeting_id=meeting_id, full_text=full_text, language=language)
        db.session.add(t)
        db.session.commit()
        return t

    @staticmethod
    def get_transcript(meeting_id: int) -> Transcript | None:
        return Transcript.query.filter_by(meeting_id=meeting_id).first()

    # ── Résumé ─────────────────────────────────────────────────────

    @staticmethod
    def save_summary(meeting_id: int, general_summary: str,
                     participants: list, conclusion: str) -> Summary:
        general_summary = _normalize_text(general_summary)
        conclusion = _normalize_text(conclusion)
        
        existing = Summary.query.filter_by(meeting_id=meeting_id).first()
        if existing:
            existing.general_summary = general_summary
            existing.participants    = json.dumps(participants, ensure_ascii=False)
            existing.conclusion      = conclusion
            db.session.commit()
            return existing
        s = Summary(
            meeting_id=meeting_id,
            general_summary=general_summary,
            participants=json.dumps(participants, ensure_ascii=False),
            conclusion=conclusion
        )
        db.session.add(s)
        db.session.commit()
        return s

    @staticmethod
    def get_summary(meeting_id: int) -> Summary | None:
        return Summary.query.filter_by(meeting_id=meeting_id).first()

    @staticmethod
    def set_pdf_path(meeting_id: int, pdf_path: str) -> None:
        s = Summary.query.filter_by(meeting_id=meeting_id).first()
        if s:
            s.pdf_path = pdf_path
            db.session.commit()

    # ── Décisions ──────────────────────────────────────────────────

    @staticmethod
    def save_decisions(meeting_id: int, decisions: list[dict]) -> list[Decision]:
        # Supprime les anciennes avant de réinsérer
        Decision.query.filter_by(meeting_id=meeting_id).delete()
        db.session.commit()
        objects = []
        for d in decisions:
            obj = Decision(
                meeting_id=meeting_id,
                content=_normalize_text(d.get("content", "")),
                context=_normalize_text(d.get("context"))
            )
            db.session.add(obj)
            objects.append(obj)
        db.session.commit()
        return objects

    @staticmethod
    def get_decisions(meeting_id: int) -> list[Decision]:
        return Decision.query.filter_by(meeting_id=meeting_id).all()

    # ── Actions ────────────────────────────────────────────────────

    @staticmethod
    def save_actions(meeting_id: int, actions: list[dict]) -> list[Action]:
        Action.query.filter_by(meeting_id=meeting_id).delete()
        db.session.commit()
        objects = []
        for a in actions:
            obj = Action(
                meeting_id=meeting_id,
                content=_normalize_text(a.get("content", "")),
                responsible=_normalize_text(a.get("responsible")),
                deadline=_normalize_text(a.get("deadline"))
            )
            db.session.add(obj)
            objects.append(obj)
        db.session.commit()
        return objects

    @staticmethod
    def get_actions(meeting_id: int) -> list[Action]:
        return Action.query.filter_by(meeting_id=meeting_id).all()

    # ── Questions ouvertes ─────────────────────────────────────────

    @staticmethod
    def save_questions(meeting_id: int, questions: list[dict]) -> list[Question]:
        Question.query.filter_by(meeting_id=meeting_id).delete()
        db.session.commit()
        objects = []
        for q in questions:
            obj = Question(
                meeting_id=meeting_id,
                content=_normalize_text(q.get("content", "")),
                context=_normalize_text(q.get("context"))
            )
            db.session.add(obj)
            objects.append(obj)
        db.session.commit()
        return objects

    @staticmethod
    def get_questions(meeting_id: int) -> list[Question]:
        return Question.query.filter_by(meeting_id=meeting_id).all()

    # ── Risques ────────────────────────────────────────────────────

    @staticmethod
    def save_risks(meeting_id: int, risks: list[dict]) -> list[Risk]:
        Risk.query.filter_by(meeting_id=meeting_id).delete()
        db.session.commit()
        objects = []
        for r in risks:
            obj = Risk(
                meeting_id=meeting_id,
                content=_normalize_text(r.get("content", "")),
                severity=_normalize_text(r.get("severity")),
                mitigation=_normalize_text(r.get("mitigation"))
            )
            db.session.add(obj)
            objects.append(obj)
        db.session.commit()
        return objects

    @staticmethod
    def get_risks(meeting_id: int) -> list[Risk]:
        return Risk.query.filter_by(meeting_id=meeting_id).all()
