"""Routes de facturation et webhook du fournisseur de paiement."""

from flask import Blueprint, jsonify, request

from middleware.jwt import jwt_required
from services.billing_service import BillingService

billing_bp = Blueprint("billing", __name__)


@billing_bp.get("/billing/plans")
def plans():
    response, status = BillingService.plans()
    return jsonify(response), status


@billing_bp.get("/billing/subscription")
@jwt_required
def subscription(current_user):
    response, status = BillingService.current(current_user)
    return jsonify(response), status


@billing_bp.get("/billing/payments")
@jwt_required
def payments(current_user):
    response, status = BillingService.payments(current_user)
    return jsonify(response), status


@billing_bp.post("/billing/quote")
@jwt_required
def quote(current_user):
    response, status = BillingService.quote(current_user, request.get_json(silent=True) or {})
    return jsonify(response), status


@billing_bp.post("/billing/checkout")
@jwt_required
def checkout(current_user):
    response, status = BillingService.checkout(current_user, request.get_json(silent=True) or {})
    return jsonify(response), status


@billing_bp.get("/billing/payments/<payment_id>")
@jwt_required
def payment(current_user, payment_id):
    response, status = BillingService.payment(current_user, payment_id)
    return jsonify(response), status


@billing_bp.post("/webhooks/riserva")
def riserva_webhook():
    response, status = BillingService.webhook(request.get_data(cache=True), request.headers)
    return jsonify(response), status
