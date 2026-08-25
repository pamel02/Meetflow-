"""
schemas/auth_schema.py - Validation des données d'authentification
Validation légère sans dépendance externe (Marshmallow ou Pydantic optionnels).
"""

import re


def validate_register(data: dict) -> tuple[dict, list[str]]:
    """
    Valide les données d'inscription.
    Retourne (données_nettoyées, liste_erreurs).
    """
    errors = []
    cleaned = {}

    # Nom
    name = (data.get("name") or "").strip()
    if not name:
        errors.append("Le nom est requis.")
    elif len(name) < 2:
        errors.append("Le nom doit contenir au moins 2 caractères.")
    elif len(name) > 120:
        errors.append("Le nom ne doit pas dépasser 120 caractères.")
    else:
        cleaned["name"] = name

    # Email
    email = (data.get("email") or "").strip().lower()
    email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not email:
        errors.append("L'email est requis.")
    elif not re.match(email_pattern, email):
        errors.append("L'email n'est pas valide.")
    else:
        cleaned["email"] = email

    # Mot de passe
    password = data.get("password") or ""
    if not password:
        errors.append("Le mot de passe est requis.")
    elif len(password) < 8:
        errors.append("Le mot de passe doit contenir au moins 8 caractères.")
    else:
        cleaned["password"] = password

    return cleaned, errors


def validate_login(data: dict) -> tuple[dict, list[str]]:
    """Valide les données de connexion."""
    errors = []
    cleaned = {}

    email = (data.get("email") or "").strip().lower()
    if not email:
        errors.append("L'email est requis.")
    else:
        cleaned["email"] = email

    password = data.get("password") or ""
    if not password:
        errors.append("Le mot de passe est requis.")
    else:
        cleaned["password"] = password

    return cleaned, errors


def validate_update_profile(data: dict) -> tuple[dict, list[str]]:
    """Valide les données de mise à jour du profil."""
    errors = []
    cleaned = {}

    if "name" in data:
        name = (data["name"] or "").strip()
        if len(name) < 2:
            errors.append("Le nom doit contenir au moins 2 caractères.")
        else:
            cleaned["name"] = name

    if "email" in data:
        email = (data["email"] or "").strip().lower()
        email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not email:
            errors.append("L'email est requis.")
        elif not re.match(email_pattern, email):
            errors.append("L'email n'est pas valide.")
        else:
            cleaned["email"] = email

    if "language" in data:
        allowed = ["fr", "en"]
        if data["language"] not in allowed:
            errors.append(f"Langue non supportée. Valeurs : {allowed}")
        else:
            cleaned["language"] = data["language"]

    return cleaned, errors
