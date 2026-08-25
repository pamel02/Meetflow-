"""
api/health_routes.py - Routes de santé et diagnostic
GET /api/health   - Vérifie que tous les composants fonctionnent
GET /api/models   - Retourne les modèles IA chargés
"""

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/live", methods=["GET"])
def liveness_check():
    """Cheap process liveness probe; external AI services are checked by /health."""
    return jsonify({"status": "ok"}), 200


@health_bp.route("/health", methods=["GET"])
def health_check():
    """
    Vérifie l'état de tous les composants du backend.
    Utilisé par Docker healthcheck et le frontend pour détecter
    si le serveur est disponible.
    """
    status = {}
    overall_ok = True

    # Flask (si on arrive ici, Flask fonctionne)
    status["flask"] = {"ok": True, "message": "Opérationnel"}

    # Base de données
    try:
        from database.database import db
        db.session.execute(db.text("SELECT 1"))
        status["database"] = {"ok": True, "message": "SQLite connecté"}
    except Exception as e:
        status["database"] = {"ok": False, "message": str(e)}
        overall_ok = False

    # NVIDIA NIM
    try:
        from ai.nvidia_client import is_available as nvidia_ok
        ok = nvidia_ok()
        status["nvidia_nim"] = {
            "ok": ok,
            "message": "Modèle LLM disponible" if ok else "NVIDIA NIM indisponible ou non configuré"
        }
        if not ok:
            overall_ok = False
    except Exception as e:
        status["nvidia_nim"] = {"ok": False, "message": str(e)}
        overall_ok = False

    # Whisper
    try:
        from ai.whisper_model import is_available as whisper_ok
        ok = whisper_ok()
        status["whisper"] = {
            "ok": ok,
            "message": "faster-whisper installé" if ok else "faster-whisper non installé"
        }
    except Exception as e:
        status["whisper"] = {"ok": False, "message": str(e)}

    # ChromaDB
    try:
        from ai.rag import RAGService
        ok = RAGService.is_available()
        status["chromadb"] = {
            "ok": ok,
            "message": "ChromaDB opérationnel" if ok else "ChromaDB indisponible"
        }
    except Exception as e:
        status["chromadb"] = {"ok": False, "message": str(e)}

    http_status = 200 if overall_ok else 503
    return jsonify({
        "status":     "ok" if overall_ok else "degraded",
        "components": status
    }), http_status


@health_bp.route("/models", methods=["GET"])
def get_models():
    """
    Retourne les modèles IA configurés et disponibles.
    Utile pour le debugging et le frontend.
    """
    import os

    models = {
        "llm":         os.environ.get("NVIDIA_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b"),
        "embedding":   os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
        "transcriber": f"whisper-{os.environ.get('WHISPER_MODEL_SIZE', 'small')}",
    }

    try:
        from ai.nvidia_client import list_models
        available = list_models()
        models["nvidia_available"] = available
    except Exception:
        models["nvidia_available"] = []

    return jsonify({"models": models}), 200
