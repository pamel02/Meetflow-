"""
database/seed.py - Données de test pour le développement
Crée un compte utilisateur de test et quelques réunions factices.

Usage :
    python -c "from database.seed import seed; seed()"
    (depuis le dossier backend, avec le contexte Flask actif)
"""

import logging
from datetime import UTC, datetime, timedelta

logger = logging.getLogger(__name__)


def seed(app=None):
    """
    Peuple la base de données avec des données de test.
    Si app est None, tente d'importer et créer l'app.
    """
    if app is None:
        import os
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from app import create_app
        app = create_app()

    with app.app_context():
        from database.database import db
        from models.Action import Action
        from models.Decision import Decision
        from models.Meeting import Meeting, MeetingStatus
        from models.Summary import Summary
        from models.Transcript import Transcript
        from models.User import User

        # ── Utilisateur de test ───────────────────────────────────────────
        existing = User.query.filter_by(email="test@example.com").first()
        if existing:
            logger.info("Données de seed déjà présentes. Ignoré.")
            return

        user = User(name="Jaurès Wilson", email="test@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.flush()  # Pour obtenir l'id avant commit

        # ── Réunion 1 : Terminée ──────────────────────────────────────────
        m1 = Meeting(
            user_id=user.id,
            title="Kick-off Projet DigiPlus",
            description="Réunion de lancement du projet DigiPlus",
            status=MeetingStatus.COMPLETED,
            duration=2700,  # 45 minutes
            segments_count=47,
            processing_step="Traitement terminé",
            processing_progress=100,
            created_at=datetime.now(UTC) - timedelta(days=3),
            ended_at=datetime.now(UTC) - timedelta(days=3)
        )
        db.session.add(m1)
        db.session.flush()

        t1 = Transcript(
            meeting_id=m1.id,
            full_text=(
                "Bonjour à tous. Aujourd'hui nous lançons officiellement le projet DigiPlus. "
                "Le backend sera développé par Jaurès avec Flask et NVIDIA NIM. "
                "La deadline pour la phase 1 est fixée au 15 juillet. "
                "Nous avons décidé d'utiliser SQLite pour le développement et MySQL pour la production. "
                "Question ouverte : faut-il intégrer un système de notifications en temps réel ?"
            ),
            language="fr"
        )
        db.session.add(t1)

        s1 = Summary(
            meeting_id=m1.id,
            general_summary=(
                "Réunion de lancement du projet DigiPlus. L'équipe a défini les responsabilités, "
                "les technologies à utiliser et la première deadline. Le backend sera développé "
                "avec Flask et NVIDIA NIM, le frontend en React avec Vite."
            ),
            participants='["Jaurès Wilson", "Client A", "Chef de projet"]',
            conclusion="Le projet DigiPlus est officiellement lancé avec une deadline phase 1 au 15 juillet."
        )
        db.session.add(s1)

        d1 = Decision(
            meeting_id=m1.id,
            content="Utiliser SQLite en développement, MySQL en production.",
            context="Décision prise pour faciliter le déploiement local."
        )
        a1 = Action(
            meeting_id=m1.id,
            content="Développer le backend Flask avec authentification JWT.",
            responsible="Jaurès Wilson",
            deadline="15 juillet 2026"
        )
        db.session.add_all([d1, a1])

        # ── Réunion 2 : En cours de traitement ────────────────────────────
        m2 = Meeting(
            user_id=user.id,
            title="Revue de sprint – Semaine 2",
            description="Point hebdomadaire sur l'avancement du backend",
            status=MeetingStatus.ANALYZING,
            duration=1800,
            segments_count=31,
            processing_step="Extraction des décisions",
            processing_progress=75,
            created_at=datetime.now(UTC) - timedelta(hours=2)
        )
        db.session.add(m2)

        # ── Réunion 3 : En attente ────────────────────────────────────────
        m3 = Meeting(
            user_id=user.id,
            title=None,  # Titre à générer automatiquement
            description="Réunion technique non titrée",
            status=MeetingStatus.PENDING,
            created_at=datetime.now(UTC) - timedelta(minutes=10)
        )
        db.session.add(m3)

        db.session.commit()
        logger.info("✅ Seed terminé. Compte de test : test@example.com / password123")
        print("✅ Données de test créées.")
        print("   Email    : test@example.com")
        print("   Password : password123")
