"""
ai/rag.py - Système RAG (Retrieval-Augmented Generation) avec ChromaDB
Indexation des transcriptions et recherche sémantique.
"""

import logging
import os
import re
import unicodedata

from ai.chunker import split_segments_for_rag
from ai.embeddings import generate_embedding, generate_embeddings_batch

logger = logging.getLogger(__name__)

STOP_WORDS = {
    "alors", "avec", "avoir", "cette", "dans", "elle", "elles", "entre", "etre",
    "faire", "leurs", "mais", "nous", "pour", "plus", "quel", "quelle", "quels",
    "quelles", "reunion", "reunions", "sans", "sont", "sur", "toutes", "tout", "une",
    "vous", "votre", "quand", "quoi", "comment", "est", "des", "les", "qui", "que",
}


def _tokens(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFKD", text.lower())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return {token for token in re.findall(r"[a-z0-9]{3,}", normalized) if token not in STOP_WORDS}


def _lexical_search(meetings, query: str, n_results: int) -> list[dict]:
    """Recherche de secours dans les transcriptions stockées en SQLite."""
    from repositories.summary_repository import SummaryRepository

    query_tokens = _tokens(query)
    candidates = []
    for meeting in meetings:
        transcript = SummaryRepository.get_transcript(meeting.id)
        if not transcript or not transcript.full_text:
            continue
        for chunk in split_segments_for_rag(transcript.full_text, meeting.id, meeting.title):
            overlap = len(query_tokens & _tokens(chunk["text"]))
            candidates.append({
                "text": chunk["text"],
                "meeting_id": meeting.id,
                "meeting_title": meeting.title,
                "chunk_index": chunk["chunk_index"],
                "relevance": round(overlap / max(len(query_tokens), 1), 4),
                "_score": overlap,
            })

    candidates.sort(key=lambda item: (item["_score"], item["relevance"]), reverse=True)
    selected = candidates[:n_results]
    for item in selected:
        item.pop("_score", None)
    return selected

CHROMA_PERSIST_DIR    = os.environ.get("CHROMA_PERSIST_DIR", "./data/chroma")
CHROMA_COLLECTION_NAME = os.environ.get("CHROMA_COLLECTION_NAME", "reunions")

# Client ChromaDB (singleton)
_chroma_client = None
_collection    = None


def _get_collection():
    """Retourne la collection ChromaDB (initialisation paresseuse)."""
    global _chroma_client, _collection

    if _collection is not None:
        return _collection

    try:
        import chromadb
        from chromadb.config import Settings

        os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)

        _chroma_client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False)
        )

        # Utilise une fonction d'embedding personnalisée (via Ollama)
        _collection = _chroma_client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

        logger.info(f"Collection ChromaDB '{CHROMA_COLLECTION_NAME}' prête.")

    except ImportError:
        logger.error("chromadb n'est pas installé. pip install chromadb")
        raise

    return _collection


class RAGService:

    @staticmethod
    def index_meeting(meeting_id: int, transcript_text: str,
                      meeting_title: str = None) -> int:
        """
        Indexe la transcription d'une réunion dans ChromaDB.
        Découpe en chunks, génère les embeddings, stocke dans Chroma.

        Returns:
            Nombre de chunks indexés.
        """
        collection = _get_collection()

        # Supprime les anciens chunks de cette réunion avant réindexation
        RAGService.delete_meeting_embeddings(meeting_id)

        # Découpe en chunks enrichis de métadonnées
        chunks = split_segments_for_rag(transcript_text, meeting_id, meeting_title)

        if not chunks:
            logger.warning(f"Aucun chunk généré pour la réunion {meeting_id}.")
            return 0

        texts       = [c["text"]         for c in chunks]
        ids         = [c["id"]           for c in chunks]
        metadatas   = [{
            "meeting_id":    c["meeting_id"],
            "meeting_title": c["meeting_title"],
            "chunk_index":   c["chunk_index"],
        } for c in chunks]

        # Génère les embeddings via Ollama
        logger.info(f"Génération de {len(chunks)} embeddings pour réunion {meeting_id}...")
        embeddings = generate_embeddings_batch(texts)

        # Filtre les chunks dont l'embedding a échoué
        valid = [
            (ids[i], texts[i], metadatas[i], embeddings[i])
            for i in range(len(chunks))
            if embeddings[i]
        ]

        if not valid:
            logger.error(f"Aucun embedding valide pour réunion {meeting_id}.")
            return 0

        v_ids, v_texts, v_metas, v_embeds = zip(*valid, strict=False)

        collection.add(
            ids=list(v_ids),
            documents=list(v_texts),
            metadatas=list(v_metas),
            embeddings=list(v_embeds)
        )

        logger.info(f"Réunion {meeting_id} : {len(valid)} chunks indexés dans ChromaDB.")
        return len(valid)

    @staticmethod
    def search_global(user_id: int, query: str, n_results: int = 5) -> list[dict]:
        """
        Recherche sémantique dans TOUTES les réunions d'un utilisateur.
        Note : ChromaDB ne filtre pas par user_id nativement.
        On utilise une collection commune et on filtre sur meeting_id
        via les meetings appartenant à l'utilisateur.
        """
        # Récupère les meeting_ids de l'utilisateur
        from repositories.meeting_repository import MeetingRepository
        meetings = MeetingRepository.find_all_by_user(user_id=user_id)
        meeting_ids = [str(m.id) for m in meetings]

        if not meeting_ids:
            return []

        try:
            collection = _get_collection()
            if collection.count() == 0:
                return _lexical_search(meetings, query, n_results)
            query_emb = generate_embedding(query)
            results = collection.query(
                query_embeddings=[query_emb],
                n_results=min(n_results, collection.count() or 1),
                where={"meeting_id": {"$in": [m.id for m in meetings]}}
                if len(meetings) > 0 else None
            )
        except Exception as e:
            logger.warning("Recherche sémantique indisponible, repli SQLite : %s", e)
            return _lexical_search(meetings, query, n_results)

        return RAGService._format_results(results)

    @staticmethod
    def search_meeting(meeting_id: int, query: str, n_results: int = 5) -> list[dict]:
        """Recherche sémantique dans UNE réunion spécifique."""
        from repositories.meeting_repository import MeetingRepository
        meeting = MeetingRepository.find_by_id(meeting_id)
        meetings = [meeting] if meeting else []

        try:
            collection = _get_collection()
            if collection.count() == 0:
                return _lexical_search(meetings, query, n_results)
            query_emb = generate_embedding(query)
            results = collection.query(
                query_embeddings=[query_emb],
                n_results=min(n_results, collection.count() or 1),
                where={"meeting_id": meeting_id}
            )
        except Exception as e:
            logger.warning("Recherche sémantique indisponible pour %s, repli SQLite : %s", meeting_id, e)
            return _lexical_search(meetings, query, n_results)

        return RAGService._format_results(results)

    @staticmethod
    def delete_meeting_embeddings(meeting_id: int) -> None:
        """Supprime tous les chunks d'une réunion de ChromaDB."""
        try:
            collection = _get_collection()
            collection.delete(where={"meeting_id": meeting_id})
            logger.info(f"Embeddings supprimés pour réunion {meeting_id}.")
        except Exception as e:
            logger.warning(f"Impossible de supprimer les embeddings de {meeting_id} : {e}")

    @staticmethod
    def _format_results(chroma_results: dict) -> list[dict]:
        """Formate les résultats ChromaDB en liste de dicts lisibles."""
        formatted = []
        documents  = chroma_results.get("documents", [[]])[0]
        metadatas  = chroma_results.get("metadatas", [[]])[0]
        distances  = chroma_results.get("distances", [[]])[0]

        for text, meta, dist in zip(documents, metadatas, distances, strict=False):
            formatted.append({
                "text":          text,
                "meeting_id":    meta.get("meeting_id"),
                "meeting_title": meta.get("meeting_title"),
                "chunk_index":   meta.get("chunk_index"),
                "relevance":     round(1 - dist, 4),  # Cosine : plus proche = plus pertinent
            })

        return formatted

    @staticmethod
    def is_available() -> bool:
        """Vérifie si ChromaDB est accessible."""
        try:
            _get_collection()
            return True
        except Exception:
            return False
