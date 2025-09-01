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


def requires_pro_plan(feature_name=None):
    """Decorator to require pro plan for workspace features"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            workspace = get_current_workspace()

            # Trust webhook-updated database state for billing checks
            # Webhooks handle real-time subscription updates

            if not workspace.is_pro:
                # Check if this is an API request
                if request.is_json or request.path.startswith("/api/"):
                    return jsonify(
                        {
                            "error": "Pro plan required",
                            "feature": feature_name,
                            "upgrade_url": f"/workspace/{workspace.id}/upgrade",
                        }
                    ), 402  # Payment Required
                else:
                    # For web requests, redirect to upgrade page
                    return redirect(
                        url_for("portal.upgrade_workspace", workspace_id=workspace.id)
                    )

            return f(*args, **kwargs)

        return decorated_function

    return decorator


class PlanLimits:
    """Simple limits helper for workspace plans"""

    @staticmethod
    def can_add_member(workspace):
        """Free: 3 members, Pro: unlimited"""
        if workspace.is_pro:
            return True
        return len(workspace.memberships) < 3

    @staticmethod
    def max_members(workspace):
        """Get max members display text"""
        return "Unlimited" if workspace.is_pro else "3"
