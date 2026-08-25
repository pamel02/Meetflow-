"""
ai/chunker.py - Découpage du texte en chunks pour le traitement LLM et RAG
Les transcriptions longues doivent être découpées avant traitement.
"""

import re


def chunk_text(text: str, chunk_size: int = 1500,
               overlap: int = 150) -> list[str]:
    """
    Découpe un texte en chunks de taille fixe avec chevauchement.
    Le chevauchement évite de perdre le contexte aux frontières.

    Args:
        text:       Texte à découper.
        chunk_size: Taille cible en caractères (≈ 300-400 tokens selon le texte).
        overlap:    Chevauchement en caractères entre deux chunks consécutifs.
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []

    chunks = []
    start  = 0

    while start < len(text):
        end = start + chunk_size

        if end < len(text):
            # Cherche une fin de phrase pour couper proprement
            boundary = _find_sentence_boundary(text, end)
            if boundary > start:
                end = boundary

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Avance avec chevauchement
        start = end - overlap

    return chunks


def _find_sentence_boundary(text: str, position: int,
                             search_window: int = 200) -> int:
    """
    Cherche la fin de phrase la plus proche d'une position donnée.
    Cela évite de couper en plein milieu d'une phrase.
    """
    window_start = max(0, position - search_window)
    window_end   = min(len(text), position + search_window)
    window       = text[window_start:window_end]

    # Cherche les délimiteurs de phrase
    for pattern in [r'[.!?]\s', r'\n\n', r'\n']:
        matches = list(re.finditer(pattern, window))
        if matches:
            # Prend le match le plus proche de `position`
            target = position - window_start
            best   = min(matches, key=lambda m: abs(m.start() - target))
            return window_start + best.end()

    return position


def split_segments_for_rag(transcript_text: str,
                           meeting_id: int,
                           meeting_title: str = None) -> list[dict]:
    """
    Prépare les chunks pour l'indexation dans ChromaDB.
    Chaque chunk est enrichi de métadonnées pour faciliter le RAG.

    Retourne une liste de dicts :
        { id, text, meeting_id, meeting_title, chunk_index }
    """
    chunks = chunk_text(transcript_text, chunk_size=1000, overlap=100)
    result = []

    for i, chunk in enumerate(chunks):
        result.append({
            "id":            f"meeting_{meeting_id}_chunk_{i}",
            "text":          chunk,
            "meeting_id":    meeting_id,
            "meeting_title": meeting_title or f"Réunion #{meeting_id}",
            "chunk_index":   i,
        })

    return result


def merge_segment_transcripts(transcripts: list[str],
                               overlap_seconds: int = 5) -> str:
    """
    Fusionne les transcriptions des segments audio en supprimant les doublons
    causés par le chevauchement de 5 secondes entre segments.

    Stratégie simple : on concatène les textes en cherchant les recouvrements.
    """
    if not transcripts:
        return ""
    if len(transcripts) == 1:
        return transcripts[0]

    merged = transcripts[0]

    for i in range(1, len(transcripts)):
        next_text = transcripts[i]
        if not next_text:
            continue

        # Cherche le début du prochain segment dans la fin du merge courant
        # pour supprimer les doublons dus au chevauchement
        overlap_removed = _remove_overlap(merged, next_text)
        merged = merged + " " + overlap_removed

    return merged.strip()


def _remove_overlap(existing: str, new_text: str,
                    min_overlap: int = 20) -> str:
    """
    Supprime la partie de `new_text` qui existe déjà à la fin de `existing`.
    Utilise une fenêtre glissante sur les derniers mots.
    """
    existing_words = existing.split()
    new_words      = new_text.split()

    # Cherche la plus longue séquence commune
    for window in range(min(len(existing_words), len(new_words), 50), min_overlap - 1, -1):
        tail = " ".join(existing_words[-window:])
        head = " ".join(new_words[:window])
        if tail.lower() == head.lower():
            return " ".join(new_words[window:])

    return new_text
