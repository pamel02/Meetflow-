"""
database/init_db.py - Initialisation de la base de données
Séparé de database.py pour pouvoir être importé indépendamment.
"""

import logging

logger = logging.getLogger(__name__)


def run_init(app):
    """
    Crée toutes les tables si elles n'existent pas.
    Appelé automatiquement au démarrage de l'application.
    """
    with app.app_context():
        from database.database import init_db
        init_db(app)
        logger.info("Base de données initialisée.")
