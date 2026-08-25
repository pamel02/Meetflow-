"""
middleware/error_handler.py - Gestionnaires d'erreurs globaux Flask
Aucun écran blanc ne doit apparaître côté frontend.
"""

from flask import current_app, jsonify


def register_error_handlers(app):
    """Enregistre tous les gestionnaires d'erreurs HTTP sur l'application."""

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Requête invalide", "detail": str(e)}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"error": "Non authentifié"}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"error": "Accès refusé"}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Ressource introuvable"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Méthode HTTP non autorisée"}), 405

    @app.errorhandler(413)
    def payload_too_large(e):
        return jsonify({"error": "Fichier trop volumineux (100 Mo max)"}), 413

    @app.errorhandler(422)
    def unprocessable(e):
        return jsonify({"error": "Données non traitables", "detail": str(e)}), 422

    @app.errorhandler(500)
    def internal_error(e):
        payload = {"error": "Erreur interne du serveur"}
        if current_app.debug:
            payload["detail"] = str(e)
        return jsonify(payload), 500

    @app.errorhandler(503)
    def service_unavailable(e):
        return jsonify({"error": "Service temporairement indisponible"}), 503
