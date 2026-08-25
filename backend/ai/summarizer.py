"""
ai/summarizer.py - Génération du bilan structuré JSON via NVIDIA NIM

Économie de tokens :
  - Un seul appel LLM pour tout le bilan (résumé + décisions + actions + questions + risques).
  - Prompts .md minimalistes (pas de markdown inutile dans les instructions).
  - Le texte envoyé au LLM est du texte brut compressé (pas de balises).
  - Pour les très longues réunions : map-reduce sur des résumés partiels légers
    avant l'appel final.

Seuil map-reduce : ~8 000 caractères.
"""

import json
import logging
import os

from ai.chunker import chunk_text
from ai.nvidia_client import NvidiaNimClient

logger = logging.getLogger(__name__)

PROMPTS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prompts")
)

# Seuil en caractères au-delà duquel on fait du map-reduce
_MAP_REDUCE_THRESHOLD = 8_000
# Taille des chunks pour le map-reduce
_CHUNK_SIZE = 4_000
# Longueur max de l'extrait envoyé pour la génération du titre
_TITLE_EXCERPT = 1_500


def _load_prompt(filename: str) -> str:
    """Charge un prompt .md depuis /prompts/. Retourne '' si absent."""
    path = os.path.join(PROMPTS_DIR, filename)
    if not os.path.exists(path):
        logger.warning(f"Prompt introuvable : {path}")
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


def _clean_json(raw: str) -> dict | list:
    """Nettoie la réponse LLM et parse le JSON."""
    raw = raw.strip()
    # Supprime les blocs ```json ... ```
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1]) if len(lines) > 2 else raw
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"JSON invalide reçu du LLM : {e}\n---\n{raw[:400]}\n---")
        return {}


def _limited_text(value, max_words: int) -> str:
    """Nettoie et borne une réponse trop verbale sans modifier son sens."""
    text = " ".join(str(value or "").split())
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]).rstrip(" ,;:") + "…"


def _normalized_items(value, fields: tuple[str, ...]) -> list[dict]:
    """Écarte les éléments mal formés, vides ou dupliqués renvoyés par le LLM."""
    if not isinstance(value, list):
        return []
    normalized, seen = [], set()
    for item in value:
        if not isinstance(item, dict):
            continue
        content = _limited_text(item.get("content"), 60)
        key = content.casefold()
        if not content or key in seen:
            continue
        seen.add(key)
        row = {"content": content}
        for field in fields:
            raw = item.get(field)
            row[field] = _limited_text(raw, 40) if raw else None
        normalized.append(row)
        if len(normalized) == 10:
            break
    return normalized


# ══════════════════════════════════════════════════════════════════════════════
# Bilan complet — un seul appel LLM
# ══════════════════════════════════════════════════════════════════════════════

def generate_full_report(transcript_text: str) -> dict:
    """
    Génère le bilan complet de la réunion en un seul appel LLM.
    Retourne un dict JSON structuré (voir schéma ci-dessous).

    Schéma de sortie :
    {
      "general_summary": str,
      "participants":    [str],
      "conclusion":      str,
      "decisions":       [{"content": str, "context": str|null}],
      "actions":         [{"content": str, "responsible": str|null, "deadline": str|null}],
      "questions":       [{"content": str, "context": str|null}],
      "risks":           [{"content": str, "severity": "faible|moyen|élevé", "mitigation": str|null}]
    }
    """
    system = _load_prompt("report.md")

    if len(transcript_text) <= _MAP_REDUCE_THRESHOLD:
        # ── Cas nominal : un seul appel ───────────────────────────────────
        prompt = _build_report_prompt(transcript_text)
    else:
        # ── Longue réunion : résumés partiels → appel final ───────────────
        prompt = _build_mapreduce_prompt(transcript_text)

    raw = NvidiaNimClient.generate(
        prompt,
        system=system,
        temperature=0.1,
        max_tokens=4096,
        enable_thinking=False,
        reasoning_budget=0,
    )
    result = _clean_json(raw)

    # Normalise les clés manquantes
    if not isinstance(result, dict):
        result = {}
    participants = result.get("participants", [])
    participants = [
        _limited_text(name, 6) for name in participants[:20]
        if isinstance(name, str) and name.strip()
    ] if isinstance(participants, list) else []
    risks = _normalized_items(result.get("risks"), ("severity", "mitigation"))
    for risk in risks:
        severity = (risk.get("severity") or "").casefold()
        risk["severity"] = {
            "faible": "faible", "moyen": "moyen", "élevé": "élevé",
            "eleve": "élevé", "haut": "élevé",
        }.get(severity, "moyen")
    return {
        "general_summary": _limited_text(result.get("general_summary"), 160),
        "participants": participants,
        "conclusion": _limited_text(result.get("conclusion"), 70),
        "decisions": _normalized_items(result.get("decisions"), ("context",)),
        "actions": _normalized_items(result.get("actions"), ("responsible", "deadline")),
        "questions": _normalized_items(result.get("questions"), ("context",)),
        "risks": risks,
    }


def _build_report_prompt(text: str) -> str:
    return (
        "Transcription:\n"
        f"{text}\n\n"
        "→ JSON:"
    )


def _build_mapreduce_prompt(text: str) -> str:
    """
    Pour les longues transcriptions :
    1. Résume chaque chunk en 2-3 phrases (appels légers).
    2. Construit le prompt final avec ces résumés condensés.
    Évite d'envoyer des milliers de tokens inutiles au LLM final.
    """
    logger.info(f"Transcription longue ({len(text)} chars) → map-reduce activé.")
    chunks = chunk_text(text, chunk_size=_CHUNK_SIZE, overlap=150)
    partials = []

    condense_system = _load_prompt("report_chunk.md")

    for i, chunk in enumerate(chunks):
        logger.info(f"Résumé partiel {i+1}/{len(chunks)}…")
        summary = NvidiaNimClient.generate(
            f"Extrais les éléments fiables de ce passage :\n{chunk}",
            system=condense_system,
            temperature=0.1,
            max_tokens=700,
            enable_thinking=False,
            reasoning_budget=0,
        )
        partials.append(summary.strip())

    condensed = "\n".join(f"[Partie {i+1}] {p}" for i, p in enumerate(partials))

    return (
        "Notes factuelles extraites des parties de la réunion. Fusionne les doublons, "
        "écarte les éléments incertains et produis le compte rendu final demandé :\n"
        f"{condensed}\n\n"
        "→ JSON complet:"
    )


# ══════════════════════════════════════════════════════════════════════════════
# Titre automatique
# ══════════════════════════════════════════════════════════════════════════════

def generate_title(transcript_text: str) -> str:
    """
    Génère un titre court (≤8 mots) pour la réunion.
    N'envoie que les 1500 premiers caractères pour économiser les tokens.
    """
    system = _load_prompt("title.md")
    excerpt = transcript_text[:_TITLE_EXCERPT]

    raw = NvidiaNimClient.generate(
        f"Transcription (extrait):\n{excerpt}\n\n→ Titre:",
        system=system,
        temperature=0.3,
        max_tokens=64,
        enable_thinking=False,
        reasoning_budget=0,
    )
    title = raw.strip().strip('"\'').strip()
    return title or "Réunion sans titre"


# ══════════════════════════════════════════════════════════════════════════════
# Compatibilité ascendante (ancienne API — conservée pour reprocess)
# ══════════════════════════════════════════════════════════════════════════════

def generate_summary(transcript_text: str) -> dict:
    """Alias vers generate_full_report pour compatibilité."""
    report = generate_full_report(transcript_text)
    return {
        "general_summary": report["general_summary"],
        "participants":    report["participants"],
        "conclusion":      report["conclusion"],
    }


def extract_structured_data(transcript_text: str) -> dict:
    """Alias vers generate_full_report pour compatibilité."""
    report = generate_full_report(transcript_text)
    return {
        "decisions": report["decisions"],
        "actions":   report["actions"],
        "questions": report["questions"],
        "risks":     report["risks"],
    }
