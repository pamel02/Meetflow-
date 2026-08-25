"""
ai/embeddings.py - Génération des embeddings via Ollama (nomic-embed-text)
Utilisé pour l'indexation dans ChromaDB et la recherche RAG.
"""

import logging
import os

import requests

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL  = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
EMBED_MODEL      = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")
OLLAMA_TIMEOUT   = int(os.environ.get("OLLAMA_TIMEOUT", "120"))


def generate_embedding(text: str) -> list[float]:
    """
    Génère un vecteur d'embedding pour un texte donné.
    Utilise nomic-embed-text via l'API Ollama.

    Returns:
        Liste de floats représentant le vecteur sémantique du texte.
    """
    if not text or not text.strip():
        raise ValueError("Le texte à embedder ne peut pas être vide.")

    url = f"{OLLAMA_BASE_URL}/api/embeddings"
    payload = {
        "model":  EMBED_MODEL,
        "prompt": text.strip(),
    }

    try:
        resp = requests.post(url, json=payload, timeout=OLLAMA_TIMEOUT)
        resp.raise_for_status()
        embedding = resp.json().get("embedding", [])
        if not embedding:
            raise ValueError("L'API Ollama a retourné un embedding vide.")
        return embedding
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Impossible de joindre Ollama pour les embeddings.")
    except requests.exceptions.Timeout:
        raise RuntimeError("Timeout lors de la génération de l'embedding.")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"Erreur HTTP Ollama embeddings : {e.response.status_code}")


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Génère des embeddings pour une liste de textes.
    Traitement séquentiel (Ollama ne supporte pas le vrai batching).
    """
    embeddings = []
    for i, text in enumerate(texts):
        try:
            emb = generate_embedding(text)
            embeddings.append(emb)
            if (i + 1) % 10 == 0:
                logger.info(f"Embeddings générés : {i+1}/{len(texts)}")
        except Exception as e:
            logger.error(f"Erreur embedding chunk {i} : {e}")
            embeddings.append([])  # Vecteur vide en cas d'erreur
    return embeddings


def is_available() -> bool:
    """Vérifie si le modèle d'embedding est disponible dans Ollama."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        models = [m["name"] for m in resp.json().get("models", [])]
        return any(EMBED_MODEL in m for m in models)
    except Exception:
        return False
