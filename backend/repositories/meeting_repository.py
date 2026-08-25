"""
repositories/meeting_repository.py - Requêtes SQL liées aux réunions
"""

from datetime import UTC, datetime

from database.database import db
from models.Meeting import Meeting, MeetingStatus
from models.Organization import Membership


class MeetingRepository:

    @staticmethod
    def create(user_id: int, organization_id: int, title: str = None, description: str = None) -> Meeting:
        """Crée une nouvelle réunion avec le statut 'pending'."""
        meeting = Meeting(
            user_id=user_id,
            organization_id=organization_id,
            title=title,
            description=description,
            status=MeetingStatus.PENDING
        )
        db.session.add(meeting)
        db.session.commit()
        return meeting

    @staticmethod
    def find_by_id(meeting_id: int) -> Meeting | None:
        return Meeting.query.get(meeting_id)

    @staticmethod
    def find_by_id_and_user(meeting_id: int, user_id: int) -> Meeting | None:
        """Récupère une réunion seulement si elle appartient à l'utilisateur."""
        membership = Membership.query.filter_by(user_id=user_id).first()
        if not membership:
            return None
        return Meeting.query.filter_by(id=meeting_id, organization_id=membership.organization_id).first()

    @staticmethod
    def find_all_by_user(user_id: int, status: str = None,
                         search: str = None, sort_by: str = "created_at",
                         sort_dir: str = "desc") -> list[Meeting]:
        """
        Liste les réunions d'un utilisateur avec filtres optionnels.
        Utilisé pour le Dashboard et la page Historique.
        """
        membership = Membership.query.filter_by(user_id=user_id).first()
        if not membership:
            return []
        query = Meeting.query.filter_by(organization_id=membership.organization_id)

        if status:
            query = query.filter(Meeting.status == status)

        if search:
            like = f"%{search}%"
            query = query.filter(
                db.or_(
                    Meeting.title.ilike(like),
                    Meeting.description.ilike(like)
                )
            )

        # Tri
        sort_column = getattr(Meeting, sort_by, Meeting.created_at)
        if sort_dir == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        return query.all()

    @staticmethod
    def get_stats_for_user(user_id: int) -> dict:
        """Calcule les statistiques du tableau de bord pour un utilisateur."""
        membership = Membership.query.filter_by(user_id=user_id).first()
        meetings = Meeting.query.filter_by(organization_id=membership.organization_id).all() if membership else []
        total = len(meetings)
        completed = sum(1 for m in meetings if m.status == MeetingStatus.COMPLETED)
        processing = sum(1 for m in meetings if m.status not in
                        [MeetingStatus.COMPLETED, MeetingStatus.ERROR, MeetingStatus.PENDING])
        total_duration = sum(m.duration or 0 for m in meetings)
        last_meeting = max(meetings, key=lambda m: m.created_at, default=None)

        return {
            "total":          total,
            "completed":      completed,
            "processing":     processing,
            "total_duration": total_duration,
            "last_meeting_at": last_meeting.created_at.isoformat() if last_meeting else None,
        }

    @staticmethod
    def update_status(meeting: Meeting, status: str,
                      step: str = None, progress: int = None) -> Meeting:
        """Met à jour le statut et la progression du traitement."""
        meeting.status = status
        if status != MeetingStatus.ERROR:
            meeting.error_message = None
        if step is not None:
            meeting.processing_step = step
        if progress is not None:
            meeting.processing_progress = progress
        db.session.commit()
        return meeting

    @staticmethod
    def update(meeting: Meeting, **kwargs) -> Meeting:
        for key, value in kwargs.items():
            if hasattr(meeting, key):
                setattr(meeting, key, value)
        db.session.commit()
        return meeting

    @staticmethod
    def mark_ended(meeting: Meeting) -> Meeting:
        meeting.ended_at = datetime.now(UTC)
        meeting.status = MeetingStatus.TRANSCRIBING
        db.session.commit()
        return meeting

    @staticmethod
    def delete(meeting: Meeting) -> None:
        """Supprime la réunion et toutes ses données liées (cascade)."""
        db.session.delete(meeting)
        db.session.commit()

    @staticmethod
    def increment_segments(meeting: Meeting) -> Meeting:
        meeting.segments_count = (meeting.segments_count or 0) + 1
        db.session.commit()
        return meeting
