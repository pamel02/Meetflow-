"""
utils/json.py - Utilitaires JSON
Sérialisation sécurisée des objets Python non-standard.
"""

import json
from datetime import date, datetime


class SafeJSONEncoder(json.JSONEncoder):
    """
    Encodeur JSON étendu gérant les types non-standards :
    datetime, date, objets SQLAlchemy avec .to_dict().
    """

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        return super().default(obj)


def safe_dumps(obj, **kwargs) -> str:
    """Sérialise un objet en JSON de manière sécurisée."""
    return json.dumps(obj, cls=SafeJSONEncoder, ensure_ascii=False, **kwargs)


def safe_loads(text: str, default=None):
    """Désérialise du JSON avec gestion d'erreur."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default
