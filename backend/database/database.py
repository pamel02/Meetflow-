"""
database/database.py - Connexion et initialisation de la base de données
Utilise SQLAlchemy comme ORM.
"""

import os
from importlib import import_module

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text

# Instance globale de SQLAlchemy
# Importée dans tous les modèles
db = SQLAlchemy()

MODEL_MODULES = (
    "models.User",
    "models.EmailVerification",
    "models.PasswordReset",
    "models.Organization",
    "models.Billing",
    "models.Meeting",
    "models.AudioSegment",
    "models.Transcript",
    "models.Summary",
    "models.Decision",
    "models.Action",
    "models.Question",
    "models.Risk",
)


def _load_models() -> None:
    """Import every model module before SQLAlchemy creates metadata."""
    for module_name in MODEL_MODULES:
        import_module(module_name)

# Racine du dossier backend/ (chemin absolu, indépendant du CWD)
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _resolve_db_url(database_url: str) -> str:
    """
    Résout les chemins SQLite relatifs en chemins absolus basés sur backend/.
    Garantit que le dossier parent existe avant la connexion.

    Exemples :
        sqlite:///./data/reunion.db  → sqlite:////abs/path/backend/data/reunion.db
        sqlite:///data/reunion.db    → sqlite:////abs/path/backend/data/reunion.db
        mysql+pymysql://...          → inchangé
    """
    if not database_url.startswith("sqlite"):
        return database_url
    if database_url in {"sqlite:///:memory:", "sqlite+pysqlite:///:memory:"}:
        return database_url

    # Extrait le chemin depuis l'URL SQLite
    # sqlite:///./data/foo.db  → ./data/foo.db
    # sqlite:////abs/path/foo.db → /abs/path/foo.db
    raw_path = database_url.replace("sqlite:///", "", 1)

    if not os.path.isabs(raw_path):
        # Chemin relatif → le résoudre depuis backend/
        raw_path = raw_path.lstrip("./")           # supprime ./ ou / en tête
        abs_path = os.path.join(_BACKEND_ROOT, raw_path)
    else:
        abs_path = raw_path

    abs_path = os.path.normpath(abs_path)

    # Crée le dossier parent si nécessaire (ex: backend/data/)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    return f"sqlite:///{abs_path}"


def init_db(app):
    """
    Initialise SQLAlchemy avec l'application Flask.
    Crée toutes les tables si elles n'existent pas.
    """
    # Résout et fixe l'URL de la base de données
    resolved_url = _resolve_db_url(app.config["DATABASE_URL"])
    app.config["SQLALCHEMY_DATABASE_URI"] = resolved_url
    db.init_app(app)
    _load_models()

    # Import des modèles pour que SQLAlchemy les découvre

    # Création automatique des tables
    inspector = inspect(db.engine)
    is_first_organization_migration = "memberships" not in set(inspector.get_table_names())
    db.create_all()

    meeting_columns = {column["name"] for column in inspect(db.engine).get_columns("meetings")}
    if "organization_id" not in meeting_columns:
        db.session.execute(text("ALTER TABLE meetings ADD COLUMN organization_id INTEGER"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS ix_meetings_organization_id ON meetings (organization_id)"))
        db.session.commit()

    from models.Billing import Plan
    plan_definitions = (
        ("starter", "Starter", 1000, 5, 120),
        ("business", "Business", 1500, 25, 250),
        ("enterprise", "Enterprise", 2000, 100, 400),
    )
    for code, name, amount, members, minutes in plan_definitions:
        plan = Plan.query.filter_by(code=code).first()
        if plan is None:
            plan = Plan(code=code)
            db.session.add(plan)
        plan.name, plan.amount_xaf = name, amount
        plan.max_members, plan.transcription_minutes, plan.active = members, minutes, True
    db.session.commit()

    if is_first_organization_migration:
        from models.Meeting import Meeting
        from models.Organization import Membership, Organization
        from models.User import User
        for user in User.query.all():
            organization = Organization(name=f"Espace de {user.name}", created_by=user.id)
            db.session.add(organization)
            db.session.flush()
            db.session.add(Membership(organization_id=organization.id, user_id=user.id, role="admin"))
            Meeting.query.filter_by(user_id=user.id, organization_id=None).update({"organization_id": organization.id})
        db.session.commit()
