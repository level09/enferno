"""
Production-ready Stripe webhook handler following best practices
"""

import stripe
from flask import Blueprint, current_app, request

from enferno.extensions import db
from enferno.user.models import Workspace

webhooks_bp = Blueprint("webhooks", __name__)

# Track processed events to prevent duplicates
processed_events = set()


@webhooks_bp.route("/stripe/webhook", methods=["POST"])
def stripe_webhook():
    """Handle essential Stripe events following best practices"""
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature")
    secret = current_app.config.get("STRIPE_WEBHOOK_SECRET")

    if not secret:
        current_app.logger.error("Stripe webhook secret not configured")
        return "Webhook secret not configured", 500

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, secret)
    except ValueError as e:
        current_app.logger.error(f"Invalid webhook payload: {e}")
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError as e:
        current_app.logger.error(f"Invalid webhook signature: {e}")
        return "Invalid signature", 400

    event_id = event.get("id")

    # Idempotency: Skip if already processed
    if event_id in processed_events:
        current_app.logger.info(f"Skipping duplicate event {event_id}")
        return "OK", 200

    processed_events.add(event_id)

    # Keep only recent events in memory (prevent memory leak)
    if len(processed_events) > 1000:
        processed_events.clear()

    # Handle successful checkout (initial upgrade)
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata") or {}
        workspace_id = metadata.get("workspace_id")

        try:
            current_app.logger.info(
                "Webhook checkout.session.completed",
                extra={
                    "session_id": session.get("id"),
                    "subscription": session.get("subscription"),
                    "customer": session.get("customer"),
                },
            )
        except Exception:
            pass

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
        status = subscription.get("status")

        # Find and downgrade workspace
        workspace = db.session.execute(
            db.select(Workspace).where(Workspace.stripe_customer_id == customer_id)
        ).scalar_one_or_none()

        if workspace:
            try:
                workspace.plan = "free"
                db.session.commit()
                try:
                    current_app.logger.info(
                        "Downgraded workspace to free plan",
                        extra={"workspace_id": workspace.id, "sub_status": status},
                    )
                except Exception:
                    pass
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(
                    f"Failed to downgrade workspace {workspace.id} to free: {e}"
                )

    # Handle subscription reactivation
    elif event["type"] == "customer.subscription.created":
        subscription = event["data"]["object"]
        customer_id = subscription["customer"]
        status = subscription.get("status")

        workspace = db.session.execute(
            db.select(Workspace).where(Workspace.stripe_customer_id == customer_id)
        ).scalar_one_or_none()

        if workspace:
            try:
                workspace.plan = "pro"
                db.session.commit()
                try:
                    current_app.logger.info(
                        "Upgraded workspace to pro plan",
                        extra={"workspace_id": workspace.id, "sub_status": status},
                    )
                except Exception:
                    pass
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(
                    f"Failed to upgrade workspace {workspace.id} to pro: {e}"
                )

    # Handle payment failures - downgrade immediately
    elif event["type"] == "invoice.payment_failed":
        invoice = event["data"]["object"]
        customer_id = invoice["customer"]
        status = invoice.get("status")

        workspace = db.session.execute(
            db.select(Workspace).where(Workspace.stripe_customer_id == customer_id)
        ).scalar_one_or_none()

        if workspace:
            try:
                workspace.plan = "free"
                db.session.commit()
                try:
                    current_app.logger.warning(
                        "Downgraded workspace due to payment failure",
                        extra={"workspace_id": workspace.id, "invoice_status": status},
                    )
                except Exception:
                    pass
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(
                    f"Failed to downgrade workspace {workspace.id} after payment failure: {e}"
                )

    else:
        current_app.logger.info(f"Unhandled webhook event type: {event['type']}")

    return "OK", 200
