"""
Ultra-minimal Stripe billing service using hosted solutions
"""

from datetime import datetime

import stripe
from flask import current_app

from enferno.extensions import db
from enferno.user.models import Workspace


class HostedBilling:
    """Minimal billing service using Stripe's hosted pages"""

    @staticmethod
    def create_upgrade_session(workspace_id, user_email, base_url):
        """Create Stripe Checkout session for workspace upgrade"""
        stripe.api_key = current_app.config.get("STRIPE_SECRET_KEY")

        price_id = current_app.config.get("STRIPE_PRO_PRICE_ID")
        print(f"DEBUG: Creating session with price_id: {price_id}")
        print(f"DEBUG: User email: {user_email}")
        print(
            f"DEBUG: Success URL: {base_url}billing/success?session_id={{CHECKOUT_SESSION_ID}}"
        )

        try:
            session = stripe.checkout.Session.create(
                customer_email=user_email,
                line_items=[
                    {
                        "price": price_id,
                        "quantity": 1,
                    }
                ],
                mode="subscription",
                success_url=f"{base_url}billing/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{base_url}dashboard",
                metadata={"workspace_id": str(workspace_id)},
            )
            print(f"DEBUG: Successfully created session: {session.id}")
            return session
        except stripe.error.StripeError as e:
            print(f"DEBUG: Stripe error: {e}")
            raise

    @staticmethod
    def create_portal_session(customer_id, workspace_id, base_url):
        """Create Stripe Customer Portal session for billing management"""
        stripe.api_key = current_app.config.get("STRIPE_SECRET_KEY")

        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{base_url}workspace/{workspace_id}/settings",
        )
        return session

    @staticmethod
    def handle_successful_payment(session_id):
        """Handle successful Stripe payment"""

        stripe.api_key = current_app.config.get("STRIPE_SECRET_KEY")

        print(f"DEBUG: Processing payment for session {session_id}")

        try:
            # Retrieve session from Stripe
            session = stripe.checkout.Session.retrieve(session_id)
            workspace_id = session.metadata.get("workspace_id")

            print(
                f"DEBUG: Session details - workspace_id: {workspace_id}, customer: {session.customer}, payment_status: {session.payment_status}"
            )

            if workspace_id:
                # Update workspace to Pro
                workspace = db.session.get(Workspace, int(workspace_id))
                if workspace:
                    print(
                        f"DEBUG: Found workspace {workspace.id}, current plan: {workspace.plan}"
                    )
                    workspace.plan = "pro"
                    workspace.stripe_customer_id = session.customer
                    workspace.upgraded_at = datetime.utcnow()
                    db.session.commit()
                    print(f"DEBUG: Upgraded workspace {workspace.id} to pro plan")

                    return True
                else:
                    print(f"DEBUG: Workspace {workspace_id} not found")
            else:
                print("DEBUG: No workspace_id in session metadata")
        except Exception as e:
            print(f"DEBUG: Error processing payment: {e}")

        return False

    @staticmethod
    def sync_workspace_subscription(workspace):
        """Actively check Stripe subscription status and sync workspace"""
        if not workspace.stripe_customer_id:
            print(
                f"DEBUG: Workspace {workspace.id} has no stripe_customer_id, staying {workspace.plan}"
            )
            return workspace.plan

        stripe.api_key = current_app.config.get("STRIPE_SECRET_KEY")

        print(
            f"DEBUG: Syncing workspace {workspace.id} (customer: {workspace.stripe_customer_id})"
        )

        try:
            # Simple: Just check for active subscriptions
            subscriptions = stripe.Subscription.list(
                customer=workspace.stripe_customer_id, status="active", limit=1
            )

            current_plan = "pro" if subscriptions.data else "free"
            print(
                f"DEBUG: Found {len(subscriptions.data)} active subscriptions, plan should be: {current_plan}"
            )

            # Update if changed
            if workspace.plan != current_plan:
                print(
                    f"DEBUG: Updating workspace {workspace.id} plan: {workspace.plan} -> {current_plan}"
                )
                workspace.plan = current_plan

                db.session.commit()

            return current_plan

        except Exception as e:
            print(f"DEBUG: Error syncing workspace {workspace.id}: {e}")
            # On any error, trust current database value
            return workspace.plan
