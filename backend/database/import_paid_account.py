"""Importe un compte payé depuis une base SQLite MeetFlow sans écraser la cible."""

import argparse
import os
import sqlite3
from datetime import datetime

from app import create_app
from database.database import db
from models.Billing import Payment, Plan, Subscription
from models.EmailVerification import EmailVerification
from models.Organization import Membership, Organization
from models.User import User


def parse_datetime(value):
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    return parsed.replace(tzinfo=None)


def source_row(connection, query, parameters=()):
    return connection.execute(query, parameters).fetchone()


def import_account(source_path, email):
    source_path = os.path.realpath(source_path)
    if not os.path.isfile(source_path):
        raise RuntimeError(f"Base source introuvable : {source_path}")

    source = sqlite3.connect(f"file:{source_path}?mode=ro", uri=True)
    source.row_factory = sqlite3.Row
    normalized_email = email.strip().lower()

    try:
        source_user = source_row(
            source,
            "SELECT * FROM users WHERE lower(email) = ?",
            (normalized_email,),
        )
        if not source_user:
            raise RuntimeError("Compte introuvable dans la base source.")

        source_organization = source_row(
            source,
            """
            SELECT o.*, m.role, m.joined_at
            FROM memberships m
            JOIN organizations o ON o.id = m.organization_id
            WHERE m.user_id = ?
            ORDER BY m.id
            LIMIT 1
            """,
            (source_user["id"],),
        )
        if not source_organization:
            raise RuntimeError("Aucune entreprise associée au compte source.")

        source_subscription = source_row(
            source,
            """
            SELECT s.*, p.code AS plan_code
            FROM subscriptions s
            JOIN plans p ON p.id = s.plan_id
            WHERE s.organization_id = ? AND s.status = 'ACTIVE'
            LIMIT 1
            """,
            (source_organization["id"],),
        )
        if not source_subscription:
            raise RuntimeError("Aucun abonnement actif dans la base source.")

        completed_payments = source.execute(
            """
            SELECT pay.*, p.code AS plan_code
            FROM payments pay
            JOIN plans p ON p.id = pay.plan_id
            WHERE pay.organization_id = ? AND pay.status = 'COMPLETED'
            ORDER BY pay.created_at
            """,
            (source_organization["id"],),
        ).fetchall()
        if not completed_payments:
            raise RuntimeError("Aucun paiement confirmé dans la base source.")

        verification = source_row(
            source,
            "SELECT * FROM email_verifications WHERE user_id = ?",
            (source_user["id"],),
        )

        if User.query.filter(db.func.lower(User.email) == normalized_email).first():
            raise RuntimeError("Ce compte existe déjà dans la base cible ; import annulé.")

        target_plan = Plan.query.filter_by(code=source_subscription["plan_code"]).first()
        if not target_plan:
            raise RuntimeError("L'offre source n'existe pas dans la base cible.")

        user = User(
            name=source_user["name"],
            email=normalized_email,
            password_hash=source_user["password_hash"],
            language=source_user["language"],
            created_at=parse_datetime(source_user["created_at"]),
            updated_at=parse_datetime(source_user["updated_at"]),
        )
        db.session.add(user)
        db.session.flush()

        organization = Organization(
            name=source_organization["name"],
            sector=source_organization["sector"],
            company_size=source_organization["company_size"],
            country=source_organization["country"],
            created_by=user.id,
            created_at=parse_datetime(source_organization["created_at"]),
            updated_at=parse_datetime(source_organization["updated_at"]),
        )
        db.session.add(organization)
        db.session.flush()
        db.session.add(Membership(
            organization_id=organization.id,
            user_id=user.id,
            role=source_organization["role"],
            joined_at=parse_datetime(source_organization["joined_at"]),
        ))

        subscription = Subscription(
            organization_id=organization.id,
            plan_id=target_plan.id,
            status=source_subscription["status"],
            current_period_start=parse_datetime(source_subscription["current_period_start"]),
            current_period_end=parse_datetime(source_subscription["current_period_end"]),
            created_at=parse_datetime(source_subscription["created_at"]),
            updated_at=parse_datetime(source_subscription["updated_at"]),
        )
        db.session.add(subscription)
        db.session.flush()

        for source_payment in completed_payments:
            payment_plan = Plan.query.filter_by(code=source_payment["plan_code"]).first()
            if not payment_plan:
                raise RuntimeError(f"Offre inconnue : {source_payment['plan_code']}")
            duplicate = Payment.query.filter(
                (Payment.id == source_payment["id"])
                | (Payment.provider_payment_id == source_payment["provider_payment_id"])
            ).first()
            if duplicate:
                raise RuntimeError("Le paiement confirmé existe déjà dans la base cible.")
            db.session.add(Payment(
                id=source_payment["id"],
                organization_id=organization.id,
                plan_id=payment_plan.id,
                subscription_id=subscription.id,
                provider_payment_id=source_payment["provider_payment_id"],
                provider_company_id=source_payment["provider_company_id"],
                idempotency_key=source_payment["idempotency_key"],
                status=source_payment["status"],
                operator=source_payment["operator"],
                phone_masked=source_payment["phone_masked"],
                amount=source_payment["amount"],
                fee=source_payment["fee"],
                currency=source_payment["currency"],
                mode=source_payment["mode"],
                failure_reason=source_payment["failure_reason"],
                created_at=parse_datetime(source_payment["created_at"]),
                completed_at=parse_datetime(source_payment["completed_at"]),
            ))

        if verification:
            db.session.add(EmailVerification(
                user_id=user.id,
                code_hash=verification["code_hash"],
                expires_at=parse_datetime(verification["expires_at"]),
                sent_at=parse_datetime(verification["sent_at"]),
                attempt_count=verification["attempt_count"],
                verified_at=parse_datetime(verification["verified_at"]),
                created_at=parse_datetime(verification["created_at"]),
                updated_at=parse_datetime(verification["updated_at"]),
            ))

        db.session.commit()
        return {
            "email": normalized_email,
            "organization": organization.name,
            "plan": target_plan.name,
            "payments": len(completed_payments),
        }
    except Exception:
        db.session.rollback()
        raise
    finally:
        source.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Chemin de la base SQLite source")
    parser.add_argument("--email", required=True, help="Compte à importer")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        result = import_account(args.source, args.email)
    print(
        f"Import réussi : {result['email']} | {result['organization']} | "
        f"{result['plan']} | {result['payments']} paiement(s) confirmé(s)"
    )


if __name__ == "__main__":
    main()
