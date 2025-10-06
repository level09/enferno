"""
Ultra-minimal Stripe billing service using hosted pages.
"""

from datetime import datetime
from functools import wraps
from typing import Any

import stripe
from flask import current_app, jsonify, redirect, request, url_for

from enferno.extensions import db
from enferno.user.models import Workspace
from enferno.utils.tenant import get_current_workspace


class HostedBilling:
    """Minimal billing service using Stripe's hosted pages."""

    @staticmethod
    def create_upgrade_session(
        workspace_id: int, user_email: str, base_url: str
    ) -> Any:
        """Create Stripe Checkout session for workspace upgrade."""
        secret = current_app.config.get("STRIPE_SECRET_KEY")
        price_id = current_app.config.get("STRIPE_PRO_PRICE_ID")
        if not secret or not price_id:
            raise RuntimeError("Stripe is not configured")
        stripe.api_key = secret

        if not base_url.endswith("/"):
            base_url = base_url + "/"

        session = stripe.checkout.Session.create(
            customer_email=user_email,
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=f"{base_url}billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}dashboard",
            metadata={"workspace_id": str(workspace_id)},
        )
        current_app.logger.info(f"Created Stripe Checkout session: {session.id}")
        return session

    @staticmethod
    def create_portal_session(
        customer_id: str, workspace_id: int, base_url: str
    ) -> Any:
        """Create Stripe Customer Portal session for billing management."""
        secret = current_app.config.get("STRIPE_SECRET_KEY")
        if not secret:
            raise RuntimeError("Stripe is not configured")
        stripe.api_key = secret

        if not base_url.endswith("/"):
            base_url = base_url + "/"

        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{base_url}workspace/{workspace_id}/settings",
        )
        current_app.logger.info(f"Created Stripe Portal session: {session.id}")
        return session

    @staticmethod
    def handle_successful_payment(session_id: str) -> int:
        """Handle successful Stripe payment by upgrading the workspace.

        Security: session_id is the security token - validated via Stripe API.

        Returns:
            Workspace ID if successful, None otherwise
        """
        secret = current_app.config.get("STRIPE_SECRET_KEY")
        if not secret:
            raise RuntimeError("Stripe is not configured")
        stripe.api_key = secret

        # Validate session with Stripe API (can't fake this)
        session = stripe.checkout.Session.retrieve(session_id)
        current_app.logger.info(
            f"Processing checkout: {session.id} status={session.status} payment={session.payment_status}"
        )

        # Verify payment actually completed
        if session.status != "complete":
            current_app.logger.warning(
                f"Checkout session not complete: {session.id} status={session.status}"
            )
            return False

        if session.payment_status not in {"paid", "no_payment_required"}:
            current_app.logger.warning(
                f"Payment not confirmed: {session.id} payment_status={session.payment_status}"
            )
            return False

        workspace_id = (session.metadata or {}).get("workspace_id")
        if not workspace_id:
            return None

        workspace = db.session.get(Workspace, int(workspace_id))
        if not workspace:
            return None

        # Idempotent: if already pro, just return success
        if workspace.plan == "pro":
            return workspace.id

        # Upgrade workspace
        workspace.plan = "pro"
        workspace.stripe_customer_id = session.customer
        workspace.upgraded_at = datetime.utcnow()
        db.session.commit()

        return workspace.id

    @staticmethod
    def get_pro_price_info():
        """Get Pro plan pricing info from Stripe"""
        secret = current_app.config.get("STRIPE_SECRET_KEY")
        price_id = current_app.config.get("STRIPE_PRO_PRICE_ID")
        if not secret or not price_id:
            return {"amount": "N/A", "currency": "USD", "interval": "month"}

        stripe.api_key = secret
        try:
            price = stripe.Price.retrieve(price_id)
            return {
                "amount": price.unit_amount / 100,  # Convert cents to dollars
                "currency": price.currency.upper(),
                "interval": price.recurring.interval if price.recurring else "one-time",
            }
        except Exception:
            return {"amount": "N/A", "currency": "USD", "interval": "month"}


def requires_pro_plan(f):
    """Require Pro plan - assumes workspace context already set by require_workspace_access"""

    @wraps(f)
    def decorated(*args, **kwargs):
        workspace = get_current_workspace()
        if not workspace or not workspace.is_pro:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "Pro plan required"}), 402
            return redirect(
                url_for("portal.upgrade_workspace", workspace_id=workspace.id)
            )
        return f(*args, **kwargs)

    return decorated
