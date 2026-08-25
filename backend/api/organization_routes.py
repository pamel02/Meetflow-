from flask import Blueprint, jsonify, request

from middleware.jwt import jwt_required
from services.organization_service import OrganizationService

organization_bp = Blueprint("organizations", __name__)


@organization_bp.route("/organizations", methods=["POST"])
@jwt_required
def create_organization(current_user):
    response, status = OrganizationService.create(current_user, request.get_json(silent=True) or {})
    return jsonify(response), status


@organization_bp.route("/organizations/current", methods=["GET"])
@jwt_required
def current_organization(current_user):
    response, status = OrganizationService.current(current_user)
    return jsonify(response), status


@organization_bp.route("/organizations/members", methods=["GET"])
@jwt_required
def members(current_user):
    response, status = OrganizationService.members(current_user)
    return jsonify(response), status


@organization_bp.route("/organizations/invitations", methods=["POST"])
@jwt_required
def invite(current_user):
    response, status = OrganizationService.invite(current_user, request.get_json(silent=True) or {})
    return jsonify(response), status


@organization_bp.route("/organizations/members/<int:membership_id>", methods=["PATCH"])
@jwt_required
def update_role(current_user, membership_id):
    response, status = OrganizationService.update_member_role(current_user, membership_id, request.get_json(silent=True) or {})
    return jsonify(response), status


@organization_bp.route("/organizations/members/<int:membership_id>", methods=["DELETE"])
@jwt_required
def remove_member(current_user, membership_id):
    response, status = OrganizationService.remove_member(current_user, membership_id)
    return jsonify(response), status
