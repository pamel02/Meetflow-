"""Client NVIDIA NIM compatible avec l'API OpenAI pour toutes les tâches LLM."""

import json
import logging
import os
from collections.abc import Iterator

from openai import OpenAI, OpenAIError

logger = logging.getLogger(__name__)

NVIDIA_BASE_URL = os.environ.get(
    "NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"
).rstrip("/")
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "").strip()
NVIDIA_MODEL = os.environ.get(
    "NVIDIA_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b"
)
NVIDIA_TIMEOUT = float(os.environ.get("NVIDIA_TIMEOUT", "300"))
NVIDIA_MAX_RETRIES = int(os.environ.get("NVIDIA_MAX_RETRIES", "2"))
NVIDIA_MAX_TOKENS = int(os.environ.get("NVIDIA_MAX_TOKENS", "16384"))
NVIDIA_TOP_P = float(os.environ.get("NVIDIA_TOP_P", "0.95"))
NVIDIA_ENABLE_THINKING = os.environ.get("NVIDIA_ENABLE_THINKING", "true").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
NVIDIA_REASONING_BUDGET = int(os.environ.get("NVIDIA_REASONING_BUDGET", "16384"))


def _client() -> OpenAI:
    if not NVIDIA_API_KEY:
        raise RuntimeError(
            "NVIDIA_API_KEY est absente. Ajoutez une clé NVIDIA NIM dans backend/.env."
        )
    return OpenAI(
        base_url=NVIDIA_BASE_URL,
        api_key=NVIDIA_API_KEY,
        timeout=NVIDIA_TIMEOUT,
        max_retries=NVIDIA_MAX_RETRIES,
    )


def _messages(prompt: str, system: str | None = None) -> list[dict[str, str]]:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages


def _request_options(
    prompt: str,
    system: str | None,
    temperature: float,
    stream: bool,
    max_tokens: int | None = None,
    enable_thinking: bool | None = None,
    reasoning_budget: int | None = None,
) -> dict:
    effective_thinking = (
        NVIDIA_ENABLE_THINKING if enable_thinking is None else enable_thinking
    )
    return {
        "model": NVIDIA_MODEL,
        "messages": _messages(prompt, system),
        "temperature": temperature,
        "top_p": NVIDIA_TOP_P,
        "max_tokens": max_tokens or NVIDIA_MAX_TOKENS,
        "stream": stream,
        "extra_body": {
            "chat_template_kwargs": {"enable_thinking": effective_thinking},
            "reasoning_budget": (
                NVIDIA_REASONING_BUDGET
                if reasoning_budget is None
                else reasoning_budget
            ),
        },
    }


def generate(
    prompt: str,
    system: str | None = None,
    temperature: float = 0.3,
    *,
    max_tokens: int | None = None,
    enable_thinking: bool | None = None,
    reasoning_budget: int | None = None,
) -> str:
    """Génère une réponse complète avec NVIDIA NIM."""
    try:
        completion = _client().chat.completions.create(
            **_request_options(
                prompt,
                system,
                temperature,
                stream=False,
                max_tokens=max_tokens,
                enable_thinking=enable_thinking,
                reasoning_budget=reasoning_budget,
            )
        )
    except OpenAIError as exc:
        logger.exception("Échec de l'appel NVIDIA NIM")
        raise RuntimeError(f"NVIDIA NIM est indisponible : {exc}") from exc

    if not completion.choices:
        raise RuntimeError("NVIDIA NIM a retourné une réponse vide.")
    return (completion.choices[0].message.content or "").strip()


def generate_stream(
    prompt: str, system: str | None = None, temperature: float = 0.3
) -> Iterator[str]:
    """Diffuse uniquement le contenu final; le raisonnement interne n'est pas exposé."""
    try:
        stream = _client().chat.completions.create(
            **_request_options(prompt, system, temperature, stream=True)
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except OpenAIError as exc:
        logger.exception("Échec du streaming NVIDIA NIM")
        raise RuntimeError(f"NVIDIA NIM est indisponible : {exc}") from exc


def generate_json(prompt: str, system: str | None = None) -> dict | list:
    """Génère puis parse une réponse JSON, avec nettoyage des balises Markdown."""
    raw = generate(prompt, system=system, temperature=0.1).strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1]) if len(lines) > 2 else raw
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("Réponse NVIDIA NIM non parsable en JSON : %s", exc)
        return {}


def answer_with_context(
    question: str,
    context_chunks: list[dict],
    scope: str = "global",
    meeting_title: str | None = None,
) -> str:
    """Génère une réponse à partir du contexte RAG déjà sélectionné."""
    if not context_chunks:
        return "Aucune information pertinente trouvée dans les réunions disponibles."

    chat_prompt_path = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prompts", "chat.md")
    )
    if os.path.exists(chat_prompt_path):
        with open(chat_prompt_path, encoding="utf-8") as prompt_file:
            system = prompt_file.read().strip()
    else:
        system = "Analyse les réunions. Réponds uniquement à partir du contexte."

    parts = []
    for chunk in context_chunks:
        text = chunk.get("text", "").strip()
        title = chunk.get("meeting_title") or f"Réunion #{chunk.get('meeting_id', '?')}"
        parts.append(f"[{title}]\n{text}")

    scope_label = (
        f"réunion : {meeting_title}"
        if scope == "meeting" and meeting_title
        else "toutes les réunions"
    )
    context = "\n---\n".join(parts)
    prompt = f"Contexte ({scope_label}):\n{context}\n\nQuestion: {question}"
    # Le chat doit rester interactif : le budget maximal est réservé aux bilans.
    return generate(
        prompt,
        system=system,
        temperature=0.2,
        max_tokens=2048,
        enable_thinking=False,
        reasoning_budget=0,
    )


def is_available() -> bool:
    """Vérifie la configuration et l'accès au catalogue NVIDIA sans générer de texte."""
    if not NVIDIA_API_KEY:
        return False
    try:
        models = _client().models.list()
        return any(model.id == NVIDIA_MODEL for model in models.data)
    except Exception:
        return False


def list_models() -> list[str]:
    """Retourne les modèles visibles pour la clé NVIDIA configurée."""
    if not NVIDIA_API_KEY:
        return []
    try:
        return [model.id for model in _client().models.list().data]
    except Exception:
        return []


class NvidiaNimClient:
    """Façade stable utilisée par les services applicatifs."""

    generate = staticmethod(generate)
    generate_stream = staticmethod(generate_stream)
    generate_json = staticmethod(generate_json)
    answer_with_context = staticmethod(answer_with_context)
    is_available = staticmethod(is_available)
    list_models = staticmethod(list_models)
