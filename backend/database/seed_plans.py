"""
database/seed_plans.py - Initialise les plans tarifaires en production.
Idempotent : ne crée pas de doublon si les plans existent déjà.

Usage :
    python -c "from database.seed_plans import seed_plans; seed_plans()"
    (depuis le dossier backend, avec FLASK_APP configuré)

Ou directement :
    python database/seed_plans.py
"""

import logging
import os
import sys

logger = logging.getLogger(__name__)


PLANS_DATA = [
    {
        "code": "starter",
        "name": "Starter",
        "amount_xaf": 1000,
        "max_members": 5,
        "transcription_minutes": 120,
        "active": True,
    },
    {
        "code": "business",
        "name": "Business",
        "amount_xaf": 1500,
        "max_members": 25,
        "transcription_minutes": 250,
        "active": True,
    },
    {
        "code": "enterprise",
        "name": "Enterprise",
        "amount_xaf": 2000,
        "max_members": 999,   # illimité en pratique
        "transcription_minutes": 400,
        "active": True,
    },
]


def seed_plans(app=None):
    """
    Insère ou met à jour les plans tarifaires en base de données.
    Les plans existants (même code) sont mis à jour, pas recréés.
    """
    if app is None:
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from app import create_app
        app = create_app()

    with app.app_context():
        from database.database import db
        from models.Billing import Plan

        created = 0
        updated = 0

        for plan_data in PLANS_DATA:
            existing = Plan.query.filter_by(code=plan_data["code"]).first()
            if existing:
                # Mise à jour des valeurs
                existing.name = plan_data["name"]
                existing.amount_xaf = plan_data["amount_xaf"]
                existing.max_members = plan_data["max_members"]
                existing.transcription_minutes = plan_data["transcription_minutes"]
                existing.active = plan_data["active"]
                updated += 1
                logger.info("Plan mis à jour : %s", plan_data["code"])
            else:
                plan = Plan(**plan_data)
                db.session.add(plan)
                created += 1
                logger.info("Plan créé : %s", plan_data["code"])

        db.session.commit()

        print(f"✅ Plans tarifaires synchronisés : {created} créés, {updated} mis à jour.")
        for p in Plan.query.filter_by(active=True).order_by(Plan.amount_xaf).all():
            print(
                f"   [{p.code}] {p.name} — {p.amount_xaf:,} XAF/mois "
                f"| {p.max_members} membres | {p.transcription_minutes} min"
            )


if __name__ == "__main__":
    seed_plans()
