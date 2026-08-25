"""
schemas/meeting_schema.py - Validation des données de réunion
"""


def validate_create_meeting(data: dict) -> tuple[dict, list[str]]:
    """
    Valide la création d'une réunion.
    Le titre est optionnel : le LLM le générera si absent.
    """
    errors = []
    cleaned = {}

    # Titre optionnel
    title = (data.get("title") or "").strip()
    cleaned["title"] = title if title else None  # None = génération automatique

    # Description optionnelle
    description = (data.get("description") or "").strip()
    cleaned["description"] = description if description else None

    return cleaned, errors


def validate_update_meeting(data: dict) -> tuple[dict, list[str]]:
    """Valide la mise à jour d'une réunion."""
    errors = []
    cleaned = {}

    if "title" in data:
        title = (data["title"] or "").strip()
        if len(title) > 300:
            errors.append("Le titre ne doit pas dépasser 300 caractères.")
        else:
            cleaned["title"] = title or None

    if "description" in data:
        cleaned["description"] = (data["description"] or "").strip() or None

    return cleaned, errors
