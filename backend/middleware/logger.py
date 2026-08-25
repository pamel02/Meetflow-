"""
middleware/logger.py - Middleware de journalisation des requêtes HTTP
Enregistre chaque requête entrante et sa réponse (méthode, chemin, statut, durée).
"""

import logging
import time

from flask import g, request

logger = logging.getLogger("http")


def register_request_logging(app):
    """
    Enregistre les hooks before/after request pour loguer chaque appel API.
    À appeler dans create_app() après la création de l'application.
    """

    @app.before_request
    def start_timer():
        g.start_time = time.perf_counter()

    @app.after_request
    def log_request(response):
        # Ignore les requêtes OPTIONS (preflight CORS)
        if request.method == "OPTIONS":
            return response

        elapsed = time.perf_counter() - getattr(g, "start_time", time.perf_counter())
        elapsed_ms = round(elapsed * 1000, 1)

        # Couleur dans les logs selon le statut HTTP
        status = response.status_code
        level  = logging.INFO if status < 400 else logging.WARNING if status < 500 else logging.ERROR

        logger.log(
            level,
            f"{request.method} {request.path} → {status} ({elapsed_ms}ms)"
        )

        return response
