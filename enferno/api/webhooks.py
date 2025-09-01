"""
Minimal Stripe webhook handler
"""

import stripe
from flask import Blueprint, current_app, request

from enferno.extensions import db
from enferno.user.models import Workspace

webhooks_bp = Blueprint("webhooks", __name__)


@webhooks_bp.route("/stripe/webhook", methods=["POST"])
def stripe_webhook():
    """Handle essential Stripe events"""
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature")
    secret = current_app.config.get("STRIPE_WEBHOOK_SECRET")

    if not secret:
        current_app.logger.error("Stripe webhook secret not configured")
        return "Webhook secret not configured", 500

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, secret)
    except ValueError:
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError:
        return "Invalid signature", 400

    # Handle successful checkout (initial upgrade)
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata") or {}
        workspace_id = metadata.get("workspace_id")

        current_app.logger.info(
            f"Webhook checkout.session.completed id={session.get('id')}"
        )

        if workspace_id:
            from enferno.services.billing import HostedBilling

            success = HostedBilling.handle_successful_payment(session.get("id"))
            current_app.logger.info(
                f"Processed checkout completion for workspace {workspace_id}, success={success}"
            )
        else:
            current_app.logger.warning("No workspace_id in webhook session metadata")

    # Handle subscription cancellation (most important)
    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        customer_id = subscription["customer"]

        # Find and downgrade workspace
        workspace = db.session.execute(
            db.select(Workspace).where(Workspace.stripe_customer_id == customer_id)
        ).scalar_one_or_none()

        if workspace:
            try:
                workspace.plan = "free"
                db.session.commit()
                current_app.logger.info(
                    f"Downgraded workspace {workspace.id} to free plan"
                )
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(
                    f"Failed to downgrade workspace {workspace.id} to free: {e}"
                )

    # Handle subscription reactivation
    elif event["type"] == "customer.subscription.created":
        subscription = event["data"]["object"]
        customer_id = subscription["customer"]

        workspace = db.session.execute(
            db.select(Workspace).where(Workspace.stripe_customer_id == customer_id)
        ).scalar_one_or_none()

        if workspace:
            try:
                workspace.plan = "pro"
                db.session.commit()
                current_app.logger.info(
                    f"Upgraded workspace {workspace.id} to pro plan"
                )
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(
                    f"Failed to upgrade workspace {workspace.id} to pro: {e}"
                )

    return "OK", 200
