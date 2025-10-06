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


def _init_stripe():
    """Initialize Stripe API key from config"""
    secret = current_app.config.get("STRIPE_SECRET_KEY")
    if not secret:
        raise RuntimeError("Stripe is not configured")
    stripe.api_key = secret


class HostedBilling:
    """Minimal billing service using Stripe's hosted pages."""

    @staticmethod
    def create_upgrade_session(
        workspace_id: int, user_email: str, base_url: str
    ) -> Any:
        """Create Stripe Checkout session for workspace upgrade."""
        _init_stripe()
        price_id = current_app.config.get("STRIPE_PRO_PRICE_ID")
        if not price_id:
            raise RuntimeError("Stripe price not configured")

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
        _init_stripe()
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
        _init_stripe()
        session = stripe.checkout.Session.retrieve(session_id)
        current_app.logger.info(
            f"Processing checkout: {session.id} status={session.status} payment={session.payment_status}"
        )

        # Verify payment actually completed
        if session.status != "complete":
            current_app.logger.warning(
                f"Checkout session not complete: {session.id} status={session.status}"
            )
            return None

        if session.payment_status not in {"paid", "no_payment_required"}:
            current_app.logger.warning(
                f"Payment not confirmed: {session.id} payment_status={session.payment_status}"
            )
            return None

        workspace_id = session.metadata.get("workspace_id")
        if not workspace_id:
            return None

        workspace = db.session.get(Workspace, int(workspace_id))
        if not workspace:
            return None

        # Idempotent: if already pro, just return success
        if workspace.is_pro:
            return workspace.id

        # Upgrade workspace
        try:
            workspace.plan = "pro"
            workspace.stripe_customer_id = session.customer
            workspace.upgraded_at = datetime.utcnow()
            db.session.commit()
            return workspace.id
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to upgrade workspace {workspace_id}: {e}")
            return None


def requires_pro_plan(f):
    """Require Pro plan - assumes workspace context already set by require_workspace_access"""

    @wraps(f)
    def decorated(*args, **kwargs):
        workspace = get_current_workspace()
        if not workspace:
            return jsonify({"error": "Workspace not found"}), 404
        if not workspace.is_pro:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "Pro plan required"}), 402
            return redirect(
                url_for("portal.upgrade_workspace", workspace_id=workspace.id)
            )
        return f(*args, **kwargs)

    return decorated
