"""
Ultra-minimal Stripe billing service using hosted pages.
"""

from datetime import datetime
from functools import wraps
from typing import Any

import stripe
from flask import abort, current_app, jsonify, redirect, request, url_for
from flask_security import current_user

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
        try:
            current_app.logger.info(
                "Processing checkout success",
                extra={
                    "session_id": getattr(session, "id", None),
                    "subscription": getattr(session, "subscription", None),
                    "status": getattr(session, "status", None),
                    "payment_status": getattr(session, "payment_status", None),
                },
            )
        except Exception:
            pass

        # Verify payment actually completed
        if session.status != "complete":
            try:
                current_app.logger.warning(
                    "Checkout session not complete",
                    extra={"session_id": session.id, "status": session.status},
                )
            except Exception:
                pass
            return False

        if session.payment_status not in {"paid", "no_payment_required"}:
            try:
                current_app.logger.warning(
                    "Payment not confirmed",
                    extra={
                        "session_id": session.id,
                        "payment_status": session.payment_status,
                    },
                )
            except Exception:
                pass
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


def requires_pro_plan(feature_name=None):
    """Decorator to require pro plan for workspace features"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            workspace = get_current_workspace()

            # Guard: workspace context must exist
            if workspace is None:
                if request.is_json or request.path.startswith("/api/"):
                    return jsonify({"error": "Workspace context required"}), 403
                else:
                    abort(403, "Workspace context required")

            # Re-validate user is authenticated and still has access
            if not current_user.is_authenticated:
                if request.is_json or request.path.startswith("/api/"):
                    return jsonify({"error": "Authentication required"}), 401
                else:
                    abort(401)

            if not current_user.can_access_workspace(workspace.id):
                if request.is_json or request.path.startswith("/api/"):
                    return jsonify({"error": "Access denied to workspace"}), 403
                else:
                    abort(403, "Access denied to workspace")

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
