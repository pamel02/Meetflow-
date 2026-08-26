"""Gestion des espaces entreprise, membres et invitations."""

import re
from datetime import UTC, datetime
from urllib.parse import urlencode

from flask import current_app

from database.database import db
from models.Organization import Membership, Organization, OrganizationInvitation
from repositories.user_repository import UserRepository
from services.email_service import EmailService

ROLES = {"admin", "organizer", "member", "auditor"}


class OrganizationService:
    @staticmethod
    def membership_for(user):
        return Membership.query.filter_by(user_id=user.id).first()

    @staticmethod
    def can_organize(user) -> bool:
        membership = OrganizationService.membership_for(user)
        return bool(membership and membership.role in {"admin", "organizer"})

    @staticmethod
    def create(user, data):
        if OrganizationService.membership_for(user):
            return {"error": "Vous appartenez déjà à une entreprise."}, 409
        name = (data.get("name") or "").strip()
        if len(name) < 2 or len(name) > 160:
            return {"error": "Le nom de l'entreprise doit contenir entre 2 et 160 caractères."}, 400

        organization = Organization(
            name=name,
            sector=(data.get("sector") or "").strip()[:100] or None,
            company_size=(data.get("company_size") or "").strip()[:30] or None,
            country=(data.get("country") or "").strip()[:80] or None,
            created_by=user.id,
        )
        db.session.add(organization)
        db.session.flush()
        membership = Membership(organization_id=organization.id, user_id=user.id, role="admin")
        db.session.add(membership)
        db.session.commit()
        return {"message": "Espace entreprise créé.", "organization": organization.to_dict(), "role": "admin"}, 201

    @staticmethod
    def current(user):
        membership = OrganizationService.membership_for(user)
        if not membership:
            return {"organization": None, "onboarding_required": True}, 200
        return {"organization": membership.organization.to_dict(), "role": membership.role, "onboarding_required": False}, 200

    @staticmethod
    def members(user):
        membership = OrganizationService.membership_for(user)
        if not membership:
            return {"error": "Aucun espace entreprise configuré."}, 404
        invitations = OrganizationInvitation.query.filter_by(organization_id=membership.organization_id, status="pending").all()
        return {
            "members": [item.to_dict() for item in membership.organization.memberships],
            "invitations": [item.to_dict() for item in invitations],
        }, 200

    @staticmethod
    def invite(user, data):
        membership = OrganizationService.membership_for(user)
        if not membership or membership.role != "admin":
            return {"error": "Seul un administrateur peut inviter des membres."}, 403

        from services.billing_service import BillingService
        entitlement = BillingService.entitlement(user, "member")
        if entitlement:
            return entitlement

        email = (data.get("email") or "").strip().lower()
        role = (data.get("role") or "member").strip().lower()
        if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
            return {"error": "L'adresse email n'est pas valide."}, 400
        if role not in ROLES or role == "admin":
            return {"error": "Le rôle sélectionné n'est pas valide."}, 400

        existing_user = UserRepository.find_by_email(email)
        if existing_user:
            existing_membership = Membership.query.filter_by(user_id=existing_user.id).first()
            if existing_membership:
                message = "Cette personne fait déjà partie de l'entreprise." if existing_membership.organization_id == membership.organization_id else "Cette personne appartient déjà à une autre entreprise."
                return {"error": message}, 409

        invitation = OrganizationInvitation.query.filter_by(organization_id=membership.organization_id, email=email).first()
        if invitation is None:
            invitation = OrganizationInvitation(organization_id=membership.organization_id, email=email, invited_by=user.id)
            db.session.add(invitation)
        invitation.role = role
        invitation.status = "pending"
        invitation.created_at = datetime.now(UTC)

        if existing_user:
            db.session.add(Membership(organization_id=membership.organization_id, user_id=existing_user.id, role=role))
            invitation.status = "accepted"
            invitation.accepted_at = datetime.now(UTC)
        db.session.commit()

        invitation_url = (
            f"{current_app.config['PUBLIC_APP_URL']}/invitation?"
            + urlencode({
                "email": email,
                "entreprise": membership.organization.name,
                "role": role,
            })
        )
        delivery = EmailService.send_organization_invitation(
            email,
            user.name,
            membership.organization.name,
            role,
            invitation_url,
        )
        return {
            "message": "Invitation envoyée." if delivery.get("success") else "Invitation enregistrée, mais l'email n'a pas pu être envoyé.",
            "invitation": invitation.to_dict(),
            "email_sent": bool(delivery.get("success")),
        }, 201

    @staticmethod
    def update_member_role(user, membership_id, data):
        actor = OrganizationService.membership_for(user)
        if not actor or actor.role != "admin":
            return {"error": "Action réservée aux administrateurs."}, 403
        target = Membership.query.filter_by(id=membership_id, organization_id=actor.organization_id).first()
        role = (data.get("role") or "").lower()
        if not target or role not in ROLES:
            return {"error": "Membre ou rôle invalide."}, 400
        if target.user_id == user.id and role != "admin":
            return {"error": "Vous ne pouvez pas retirer votre propre rôle administrateur."}, 400
        target.role = role
        db.session.commit()
        return {"message": "Rôle mis à jour.", "member": target.to_dict()}, 200

    @staticmethod
    def remove_member(user, membership_id):
        actor = OrganizationService.membership_for(user)
        if not actor or actor.role != "admin":
            return {"error": "Action réservée aux administrateurs."}, 403
        target = Membership.query.filter_by(id=membership_id, organization_id=actor.organization_id).first()
        if not target:
            return {"error": "Membre introuvable."}, 404
        if target.user_id == user.id:
            return {"error": "Vous ne pouvez pas vous retirer vous-même de l'entreprise."}, 400
        db.session.delete(target)
        db.session.commit()
        return {"message": "Membre retiré."}, 200

    @staticmethod
    def accept_pending_invitations(user):
        if OrganizationService.membership_for(user):
            return
        invitation = OrganizationInvitation.query.filter_by(email=user.email, status="pending").order_by(OrganizationInvitation.created_at.desc()).first()
        if invitation:
            db.session.add(Membership(organization_id=invitation.organization_id, user_id=user.id, role=invitation.role))
            invitation.status = "accepted"
            invitation.accepted_at = datetime.now(UTC)
            db.session.commit()
