from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from flask_security import auth_required, current_user

from enferno.extensions import db
from enferno.services.auth import require_superadmin_api
from enferno.user.models import Membership, User, Workspace
from enferno.utils.tenant import (
    WorkspaceService,
    get_current_workspace,
    require_workspace_access,
    set_current_workspace,
)

portal = Blueprint("portal", __name__, static_folder="../static")


@portal.before_request
@auth_required("session")
def before_request():
    pass


@portal.after_request
def add_header(response):
    response.headers["Cache-Control"] = "public, max-age=10800"
    return response


@portal.route("/dashboard/")
def dashboard():
    """Show workspace selection for user"""
    if current_user.is_superadmin:
        # Super admin sees all workspaces
        workspaces = current_user.get_workspaces()
    else:
        # Regular users only see their own workspaces
        workspaces = current_user.get_workspaces()

    # Add user role info to each workspace
    workspace_data = []
    for workspace in workspaces:
        workspace_dict = workspace.to_dict()
        workspace_dict["user_role"] = current_user.get_workspace_role(workspace.id)
        workspace_data.append(workspace_dict)

    return render_template("dashboard.html", workspaces=workspace_data)


@portal.route("/workspace/<int:workspace_id>/")
@require_workspace_access("member")
def workspace_view(workspace_id):
    """Main workspace interface"""
    workspace = get_current_workspace()
    user_role = current_user.get_workspace_role(workspace_id)
    return render_template("workspace.html", workspace=workspace, user_role=user_role)


@portal.route("/workspace/<int:workspace_id>/team/")
@require_workspace_access("admin")
def workspace_team(workspace_id):
    """Team management (admin only)"""
    workspace = get_current_workspace()
    user_role = current_user.get_workspace_role(workspace_id)
    return render_template(
        "workspace_team.html", workspace=workspace, user_role=user_role
    )


@portal.route("/workspace/<int:workspace_id>/settings/")
@require_workspace_access("member")
def workspace_settings(workspace_id):
    """Workspace settings"""
    workspace = get_current_workspace()
    user_role = current_user.get_workspace_role(workspace_id)
    return render_template(
        "workspace_settings.html", workspace=workspace, user_role=user_role
    )


@portal.route("/workspace/<int:workspace_id>/switch/")
@auth_required("session")
def switch_workspace(workspace_id):
    """Switch to a workspace"""
    # Verify user has access
    if current_user.can_access_workspace(workspace_id):
        set_current_workspace(workspace_id)
        return redirect(url_for("portal.workspace_view", workspace_id=workspace_id))
    else:
        return redirect(url_for("portal.dashboard"))


# API Endpoints
@portal.route("/api/workspaces", methods=["POST"])
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


@portal.route("/api/workspace/<int:workspace_id>/stats")
@require_workspace_access("member")
def workspace_stats(workspace_id):
    """Get workspace statistics"""
    member_count = db.session.execute(
        db.select(db.func.count(Membership.user_id)).where(
            Membership.workspace_id == workspace_id
        )
    ).scalar()

    return jsonify({"member_count": member_count or 0})


@portal.route("/api/workspace/<int:workspace_id>", methods=["PUT"])
@require_workspace_access("admin")
def workspace_update(workspace_id):
    """Update workspace details"""
    workspace = get_current_workspace()
    data = request.json

    if "name" in data:
        workspace.name = data["name"]

    try:
        db.session.commit()
        return jsonify({"message": "Workspace updated successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to update workspace", "error": str(e)}), 400


@portal.route("/api/profile", methods=["PUT"])
@auth_required("session")
def profile_update():
    """Update user profile"""
    data = request.json

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


@portal.route("/api/workspace/<int:workspace_id>/members", methods=["POST"])
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


@portal.route("/api/workspace/<int:workspace_id>/members/add", methods=["POST"])
@require_workspace_access("admin")
def add_workspace_member(workspace_id):
    """Add new member to workspace"""
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

    # Create new user
    from flask_security.utils import hash_password

    user = User(
        name=name,
        username=username,
        email=email,
        password=hash_password(password),
        active=True,
    )
    db.session.add(user)
    db.session.commit()

    # Add to workspace
    WorkspaceService.add_member(workspace_id, user, role)

    return jsonify({"message": f"{name} added to workspace"})


@portal.route(
    "/api/workspace/<int:workspace_id>/members/<int:user_id>", methods=["PUT"]
)
@require_workspace_access("admin")
def update_workspace_member(workspace_id, user_id):
    """Update member role"""
    data = request.get_json()
    new_role = data.get("role")

    if new_role not in ["admin", "member"]:
        return jsonify({"error": "Invalid role"}), 400

    success = WorkspaceService.update_member_role(workspace_id, user_id, new_role)
    if success:
        return jsonify({"message": "Role updated successfully"})
    else:
        return jsonify({"error": "Failed to update role"}), 400


@portal.route(
    "/api/workspace/<int:workspace_id>/members/<int:user_id>", methods=["DELETE"]
)
@require_workspace_access("admin")
def remove_workspace_member(workspace_id, user_id):
    """Remove member from workspace"""
    if user_id == current_user.id:
        return jsonify({"error": "Cannot remove yourself from workspace"}), 400

    success = WorkspaceService.remove_member(workspace_id, user_id)
    if success:
        return jsonify({"message": "Member removed from workspace"})
    else:
        return jsonify({"error": "Failed to remove member"}), 400


# Super Admin API Endpoints
@portal.route("/api/admin/stats")
@require_superadmin_api()
def admin_stats():
    """Get platform statistics - super admin only"""

    from datetime import datetime

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


@portal.route("/api/admin/workspaces")
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


@portal.route("/api/admin/users")
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
