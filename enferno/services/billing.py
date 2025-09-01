"""
Ultra-minimal Stripe billing service using hosted pages.
"""

from datetime import datetime
from typing import Any

import stripe
from flask import current_app

from enferno.extensions import db
from enferno.user.models import Workspace


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
        try:
            current_app.logger.info(
                "Created Stripe Checkout session",
                extra={"session_id": getattr(session, "id", None)},
            )
        except Exception:
            pass
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
        try:
            current_app.logger.info(
                "Created Stripe Portal session",
                extra={"portal_session_id": getattr(session, "id", None)},
            )
        except Exception:
            pass
        return session

    @staticmethod
    def handle_successful_payment(session_id: str) -> bool:
        """Handle successful Stripe payment by upgrading the workspace."""
        secret = current_app.config.get("STRIPE_SECRET_KEY")
        if not secret:
            raise RuntimeError("Stripe is not configured")
        stripe.api_key = secret

        session = stripe.checkout.Session.retrieve(session_id)
        try:
            current_app.logger.info(
                "Processing checkout success",
                extra={
                    "session_id": getattr(session, "id", None),
                    "subscription": getattr(session, "subscription", None),
                },
            )
        except Exception:
            pass
        workspace_id = (session.metadata or {}).get("workspace_id")
        if not workspace_id:
            return False

        workspace = db.session.get(Workspace, int(workspace_id))
        if not workspace:
            return False

        # Idempotency: no-op if already pro
        if workspace.plan == "pro":
            try:
                current_app.logger.info(
                    "Workspace already on pro plan",
                    extra={"workspace_id": workspace.id},
                )
            except Exception:
                pass
            return True

        workspace.plan = "pro"
        workspace.stripe_customer_id = session.customer
        workspace.upgraded_at = datetime.utcnow()
        db.session.commit()
        try:
            current_app.logger.info(
                "Workspace upgraded to pro",
                extra={"workspace_id": workspace.id},
            )
        except Exception:
            pass
        return True
