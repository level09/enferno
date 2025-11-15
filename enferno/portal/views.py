import time
from datetime import datetime

from flask import (
    Blueprint,
    current_app,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_security import auth_required, current_user
from flask_security.utils import hash_password

from enferno.extensions import db
from enferno.services.auth import require_superadmin_api
from enferno.services.billing import HostedBilling
from enferno.services.workspace import WorkspaceService, require_workspace_access
from enferno.user.models import Membership, User, Workspace

portal = Blueprint("portal", __name__, static_folder="../static")


@portal.before_request
@auth_required("session")
def before_request():
    """Ensure all portal routes require authentication"""
    pass


@portal.get("/dashboard/")
def dashboard():
    """Show workspace selection for user (or auto-redirect if only one)"""
    workspaces = current_user.get_workspaces()

    # Auto-redirect solo users to their workspace (make workspaces invisible)
    if len(workspaces) == 1 and not current_user.is_superadmin:
        return redirect(
            url_for("portal.switch_workspace", workspace_id=workspaces[0].id)
        )

    # Add user role to each workspace dict
    workspace_data = [
        {**ws.to_dict(), "user_role": current_user.get_workspace_role(ws.id)}
        for ws in workspaces
    ]

    return render_template("dashboard.html", workspaces=workspace_data)


@portal.get("/workspace/<int:workspace_id>/")
@require_workspace_access("member")
def workspace_view(workspace_id):
    """Main workspace interface"""
    return render_template(
        "workspace.html",
        workspace=g.current_workspace,
        user_role=g.user_workspace_role,
    )


@portal.get("/workspace/<int:workspace_id>/team/")
@require_workspace_access("admin")
def workspace_team(workspace_id):
    """Team management (admin only)"""
    return render_template(
        "workspace_team.html",
        workspace=g.current_workspace,
        user_role=g.user_workspace_role,
    )


@portal.get("/workspace/<int:workspace_id>/settings/")
@require_workspace_access("member")
def workspace_settings(workspace_id):
    """Workspace settings"""
    return render_template(
        "workspace_settings.html",
        workspace=g.current_workspace,
        user_role=g.user_workspace_role,
        pro_price=current_app.config.get("PRO_PRICE_DISPLAY", "$29"),
        pro_interval=current_app.config.get("PRO_PRICE_INTERVAL", "month"),
    )


@portal.get("/workspace/<int:workspace_id>/switch/")
@auth_required("session")
def switch_workspace(workspace_id):
    """Switch to a workspace"""
    # Verify user has access
    if current_user.get_workspace_role(workspace_id):
        session["current_workspace_id"] = workspace_id
        return redirect(url_for("portal.workspace_view", workspace_id=workspace_id))
    else:
        return redirect(url_for("portal.dashboard"))


# API Endpoints
@portal.post("/api/workspaces")
@require_superadmin_api()
def create_workspace():
    """Create new workspace - super admin only"""

    data = request.get_json()
    name = data.get("name", "").strip()

    if not name:
        return jsonify({"error": "Workspace name is required"}), 400

    try:
        workspace = WorkspaceService.create_workspace(name, current_user)
        return jsonify(
            {
                "message": "Workspace created successfully",
                "workspace": workspace.to_dict(),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@portal.get("/api/workspace/<int:workspace_id>/stats")
@require_workspace_access("member")
def workspace_stats(workspace_id):
    """Get workspace statistics"""
    member_count = db.session.execute(
        db.select(db.func.count(Membership.user_id)).where(
            Membership.workspace_id == workspace_id
        )
    ).scalar()

    return jsonify({"member_count": member_count or 0})


@portal.put("/api/workspace/<int:workspace_id>")
@require_workspace_access("admin")
def workspace_update(workspace_id):
    """Update workspace details"""
    data = request.get_json(silent=True) or {}

    if "name" in data:
        g.current_workspace.name = data["name"]

    try:
        db.session.commit()
        return jsonify({"message": "Workspace updated successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to update workspace", "error": str(e)}), 400


@portal.put("/api/profile")
@auth_required("session")
def profile_update():
    """Update user profile"""
    data = request.get_json(silent=True) or {}

    if "name" in data:
        current_user.name = data["name"]

    if "email" in data:
        current_user.email = data["email"]

    try:
        db.session.commit()
        return jsonify({"message": "Profile updated successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to update profile", "error": str(e)}), 400


@portal.post("/api/workspace/<int:workspace_id>/members")
@require_workspace_access("member")
def workspace_members(workspace_id):
    """List workspace members with pagination"""
    data = request.get_json() or {}
    options = data.get("options", {})
    page = options.get("page", 1)
    per_page = options.get("itemsPerPage", 25)

    # Get members with user info
    query = (
        db.select(Membership, User)
        .join(User)
        .where(Membership.workspace_id == workspace_id)
    )

    # Get total count
    total_count = db.session.execute(
        db.select(db.func.count()).select_from(
            db.select(Membership.user_id).where(Membership.workspace_id == workspace_id)
        )
    ).scalar()

    # Get paginated results
    memberships = db.session.execute(
        query.offset((page - 1) * per_page).limit(per_page)
    ).all()

    items = []
    for membership, user in memberships:
        items.append(
            {
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
                "role": membership.role,
                "created_at": membership.created_at.isoformat()
                if membership.created_at
                else None,
            }
        )

    return jsonify({"items": items, "total": total_count, "perPage": per_page})


@portal.post("/api/workspace/<int:workspace_id>/members/add")
@require_workspace_access("admin")
def add_workspace_member(workspace_id):
    """Add new member to workspace"""
    from sqlalchemy.exc import IntegrityError

    data = request.get_json()
    name = data.get("name")
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "member")

    if not all([name, username, email, password]):
        return jsonify(
            {"error": "Name, username, email and password are required"}
        ), 400

    # Check if user already exists (by email or username)
    existing_user = db.session.execute(
        db.select(User).where((User.email == email) | (User.username == username))
    ).scalar_one_or_none()

    if existing_user:
        # Check what already exists
        if existing_user.email == email:
            return jsonify({"error": "A user with this email already exists"}), 400
        elif existing_user.username == username:
            return jsonify({"error": "This username is already taken"}), 400

    try:
        with db.session.begin_nested():
            # Create new user
            user = User(
                name=name,
                username=username,
                email=email,
                password=hash_password(password),
                active=True,
            )
            db.session.add(user)
            db.session.flush()  # Get user.id

            # Add to workspace
            WorkspaceService.add_member(workspace_id, user, role)

        db.session.commit()
        return jsonify({"message": f"{name} added to workspace"})
    except (IntegrityError, ValueError) as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@portal.put("/api/workspace/<int:workspace_id>/members/<int:user_id>")
@require_workspace_access("admin")
def update_workspace_member(workspace_id, user_id):
    """Update member role"""
    data = request.get_json()
    new_role = data.get("role")

    if new_role not in ["admin", "member"]:
        return jsonify({"error": "Invalid role"}), 400

    try:
        success = WorkspaceService.update_member_role(workspace_id, user_id, new_role)
        if success:
            return jsonify({"message": "Role updated successfully"})
        else:
            return jsonify({"error": "Failed to update role"}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@portal.delete("/api/workspace/<int:workspace_id>/members/<int:user_id>")
@require_workspace_access("admin")
def remove_workspace_member(workspace_id, user_id):
    """Remove member from workspace"""
    if user_id == current_user.id:
        return jsonify({"error": "Cannot remove yourself from workspace"}), 400

    try:
        success = WorkspaceService.remove_member(workspace_id, user_id)
        if success:
            return jsonify({"message": "Member removed from workspace"})
        else:
            return jsonify({"error": "Failed to remove member"}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


# Super Admin API Endpoints
@portal.get("/api/admin/stats")
@require_superadmin_api()
def admin_stats():
    """Get platform statistics - super admin only"""
    today = datetime.now().date()

    # Total counts
    total_workspaces = (
        db.session.execute(db.select(db.func.count(Workspace.id))).scalar() or 0
    )

    total_users = db.session.execute(db.select(db.func.count(User.id))).scalar() or 0

    # New users today
    new_users_today = (
        db.session.execute(
            db.select(db.func.count(User.id)).where(
                db.func.date(User.created_at) == today
            )
        ).scalar()
        or 0
    )

    # Active workspaces (have members)
    active_workspaces = (
        db.session.execute(
            db.select(db.func.count(db.func.distinct(Membership.workspace_id)))
        ).scalar()
        or 0
    )

    return jsonify(
        {
            "total_workspaces": total_workspaces,
            "total_users": total_users,
            "new_users_today": new_users_today,
            "active_workspaces": active_workspaces,
        }
    )


@portal.get("/api/admin/workspaces")
@require_superadmin_api()
def admin_workspaces():
    """Get all workspaces - super admin only"""

    # Get all workspaces with owner and member count
    workspaces_query = (
        db.select(
            Workspace, User, db.func.count(Membership.user_id).label("member_count")
        )
        .join(User, Workspace.owner_id == User.id)
        .outerjoin(Membership, Workspace.id == Membership.workspace_id)
        .group_by(Workspace.id, User.id)
    )

    results = db.session.execute(workspaces_query).all()

    workspaces = []
    for workspace, owner, member_count in results:
        workspaces.append(
            {
                "id": workspace.id,
                "name": workspace.name,
                "slug": workspace.slug,
                "owner_name": owner.name,
                "owner_email": owner.email,
                "member_count": member_count or 0,
                "created_at": workspace.created_at.isoformat()
                if workspace.created_at
                else None,
            }
        )

    return jsonify({"workspaces": workspaces})


@portal.get("/api/admin/users")
@require_superadmin_api()
def admin_users():
    """Get all users with workspace counts - super admin only"""

    # Get users with workspace counts
    users_query = (
        db.select(User, db.func.count(Membership.workspace_id).label("workspace_count"))
        .outerjoin(Membership, User.id == Membership.user_id)
        .group_by(User.id)
        .order_by(User.created_at.desc())
    )

    results = db.session.execute(users_query).all()

    user_data = []
    for user, workspace_count in results:
        user_data.append(
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "workspace_count": workspace_count or 0,
                "active": user.active,
                "is_superadmin": user.is_superadmin,
                "role_display": "Super Admin" if user.is_superadmin else "User",
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login_at": user.last_login_at.isoformat()
                if user.last_login_at
                else None,
            }
        )

    return jsonify({"users": user_data})


# Billing Routes
@portal.get("/workspace/<int:workspace_id>/upgrade")
@require_workspace_access("admin")
def upgrade_workspace(workspace_id):
    """Redirect to Stripe Checkout - fully hosted"""
    current_app.logger.info(
        f"NEW UPGRADE REQUEST - workspace {workspace_id} for user {current_user.email} at {time.time()}"
    )

    workspace = g.current_workspace
    current_app.logger.debug(
        f"Current workspace plan: {workspace.plan}, stripe_customer_id: {workspace.stripe_customer_id}"
    )

    # Prevent duplicate subscriptions - redirect to billing portal if already Pro
    if workspace.is_pro:
        current_app.logger.info(
            f"Workspace {workspace_id} already on Pro plan, redirecting to billing portal"
        )
        # Only redirect if we have a customer ID, otherwise show settings
        if workspace.stripe_customer_id:
            return redirect(url_for("portal.billing_portal", workspace_id=workspace_id))
        else:
            # Pro workspace without Stripe customer (manual upgrade, legacy)
            return redirect(
                url_for("portal.workspace_settings", workspace_id=workspace_id)
            )

    try:
        session = HostedBilling.create_upgrade_session(
            workspace_id, current_user.email, request.url_root
        )
        current_app.logger.info(f"Created NEW session {session.id}")
        current_app.logger.debug(f"Session URL: {session.url}")
        current_app.logger.debug(f"Session status: {session.status}")
        return redirect(session.url)
    except Exception as e:
        current_app.logger.exception(
            f"FAILED - Error creating checkout session: {type(e).__name__}: {e}"
        )
        return jsonify(
            {"error": "Failed to create checkout session", "details": str(e)}
        ), 500


@portal.get("/workspace/<int:workspace_id>/billing")
@require_workspace_access("admin")
def billing_portal(workspace_id):
    """Redirect to Stripe Customer Portal - fully hosted"""
    workspace = g.current_workspace
    if workspace.stripe_customer_id:
        try:
            session = HostedBilling.create_portal_session(
                workspace.stripe_customer_id, workspace_id, request.url_root
            )
            return redirect(session.url)
        except Exception as e:
            error_msg = str(e)

            # Handle specific Stripe Customer Portal configuration error
            if "No configuration provided" in error_msg:
                return render_template(
                    "billing_error.html",
                    error_type="portal_config",
                    title="Customer Portal Not Configured",
                    message="The billing portal needs to be set up in Stripe.",
                    action_text="Contact Support",
                    action_url="/dashboard",
                    details="Please contact support to enable billing management features.",
                )
            else:
                return render_template(
                    "billing_error.html",
                    error_type="portal_error",
                    title="Billing Portal Error",
                    message="Unable to access billing portal at this time.",
                    action_text="Try Again Later",
                    action_url=f"/workspace/{workspace_id}/settings",
                    details=error_msg,
                )
    else:
        # No customer ID, redirect to upgrade
        return redirect(url_for("portal.upgrade_workspace", workspace_id=workspace_id))


@portal.get("/billing/success")
@auth_required("session")
def billing_success():
    """Handle successful Stripe checkout - validate and upgrade workspace"""
    session_id = request.args.get("session_id")

    if not session_id:
        return redirect("/dashboard")

    try:
        workspace_id = HostedBilling.handle_successful_payment(session_id)
        if workspace_id:
            return render_template("billing_success.html", success=True)
    except Exception as e:
        current_app.logger.error(f"Payment processing error: {str(e)}")

    return render_template("billing_error.html", error_type="payment_failed")
