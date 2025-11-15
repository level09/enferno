import stripe
from flask import Blueprint, current_app, request
from sqlalchemy.exc import IntegrityError

from enferno.extensions import db
from enferno.user.models import StripeEvent

webhooks_bp = Blueprint("webhooks", __name__)


@webhooks_bp.route("/stripe/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature")
    secret = current_app.config.get("STRIPE_WEBHOOK_SECRET")

    if not secret:
        current_app.logger.error("Stripe webhook secret not configured")
        return "Webhook secret not configured", 500

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, secret)
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        current_app.logger.error(f"Webhook error: {e}")
        return "Invalid request", 400

    # Skip duplicate events
    event_id = event.get("id")
    try:
        db.session.add(StripeEvent(event_id=event_id, event_type=event.get("type")))
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return "OK", 200

    # Handle checkout completion
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        session_id = session.get("id")

        from enferno.services.billing import HostedBilling

        HostedBilling.handle_successful_payment(session_id)
        current_app.logger.info(f"Processed checkout: {session_id}")

    # Handle subscription cancellation (downgrade to free)
    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        customer_id = subscription.get("customer")

        from enferno.user.models import Workspace

        workspace = db.session.execute(
            db.select(Workspace).where(Workspace.stripe_customer_id == customer_id)
        ).scalar_one_or_none()

        if workspace:
            workspace.plan = "free"
            db.session.commit()
            current_app.logger.info(
                f"Downgraded workspace {workspace.id} to free (subscription cancelled)"
            )

    # Handle payment failure (downgrade to free)
    elif event["type"] == "invoice.payment_failed":
        invoice = event["data"]["object"]
        customer_id = invoice.get("customer")

        from enferno.user.models import Workspace

        workspace = db.session.execute(
            db.select(Workspace).where(Workspace.stripe_customer_id == customer_id)
        ).scalar_one_or_none()

        if workspace and workspace.plan == "pro":
            workspace.plan = "free"
            db.session.commit()
            current_app.logger.warning(
                f"Downgraded workspace {workspace.id} to free (payment failed)"
            )

    return "OK", 200
