import datetime

import orjson as json
from flask import Blueprint, Response, abort, render_template, request
from flask_security import auth_required, current_user

from enferno.extensions import db
from enferno.user.models import Activity, User, Workspace

bp_user = Blueprint("users", __name__, static_folder="../static")

PER_PAGE = 25


@bp_user.before_request
@auth_required("session")
def before_request():
    # Ensure only super admins can access user management
    if not current_user.is_superadmin:
        abort(403)


@bp_user.get("/users/")
def users():
    # Get all workspaces for assignment
    workspaces = db.session.execute(db.select(Workspace)).scalars().all()
    workspace_list = [{"id": w.id, "name": w.name} for w in workspaces]

    return render_template("cms/users.html", workspaces=workspace_list)


@bp_user.get("/api/users")
def api_user():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", PER_PAGE, type=int)

    # Start with base query - this pattern makes it easy to add filters later
    query = db.select(User)

    # Paginate results
    pagination = db.paginate(query, page=page, per_page=per_page)

    # Convert users to dictionaries with workspace info
    items = []
    for user in pagination.items:
        user_dict = user.to_dict()
        # Add workspace information
        workspaces = user.get_workspaces()
        user_dict["workspace_count"] = len(workspaces)
        user_dict["workspaces"] = [
            {"id": w.id, "name": w.name, "role": user.get_workspace_role(w.id)}
            for w in workspaces[:3]
        ]  # Show first 3
        items.append(user_dict)

    # Create consistent response structure with metadata
    response_data = {
        "items": items,
        "total": pagination.total,
        "perPage": pagination.per_page,
    }

    return Response(json.dumps(response_data), content_type="application/json")


@bp_user.post("/api/user/")
def api_user_create():
    user_data = request.json.get("item", {})
    user = User()
    user.from_dict(user_data)
    # Handle super admin field separately - only allow one super admin via UI
    if "is_superadmin" in user_data and user_data["is_superadmin"]:
        # Check if another super admin already exists
        existing_super_admin = db.session.execute(
            db.select(User).where(User.is_superadmin)
        ).scalar_one_or_none()

        if existing_super_admin:
            return {
                "message": "Only one super admin is allowed. Use CLI command to create additional super admins if needed.",
                "error": "Super admin limit reached",
            }, 400

        user.is_superadmin = True
    user.confirmed_at = datetime.datetime.now()
    db.session.add(user)
    db.session.flush()  # Get user ID

    # Handle workspace assignments - simple approach
    if "workspace_ids" in user_data and not user.is_superadmin:
        from enferno.user.models import Membership

        for workspace_id in user_data.get("workspace_ids", []):
            membership = Membership(
                user_id=user.id, workspace_id=workspace_id, role="member"
            )
            db.session.add(membership)

    try:
        db.session.commit()
        # Register activity
        Activity.register(current_user.id, "User Create", user.to_dict())
        return {"message": "User successfully created!"}
    except Exception as e:
        db.session.rollback()
        return {"message": "Error creating user", "error": str(e)}, 412


@bp_user.post("/api/user/<int:id>")
def api_user_update(id):
    user = db.get_or_404(User, id)
    user_data = request.json.get("item", {})
    # Store old user data for activity log
    old_user_data = user.to_dict()
    user.from_dict(user_data)
    # Handle super admin field separately - with safeguards
    if "is_superadmin" in user_data:
        new_super_admin_status = user_data["is_superadmin"]

        # If trying to make someone super admin
        if new_super_admin_status and not user.is_superadmin:
            # Check if another super admin already exists
            existing_super_admin = db.session.execute(
                db.select(User).where(User.is_superadmin)
            ).scalar_one_or_none()

            if existing_super_admin:
                return {
                    "message": "Only one super admin is allowed. Use CLI command to create additional super admins if needed.",
                    "error": "Super admin limit reached",
                }, 400

        # If trying to remove super admin status, ensure at least one exists
        elif not new_super_admin_status and user.is_superadmin:
            super_admin_count = db.session.execute(
                db.select(db.func.count(User.id)).where(User.is_superadmin)
            ).scalar()

            if super_admin_count <= 1:
                return {
                    "message": "Cannot remove the last super admin. Create another super admin first.",
                    "error": "Cannot remove last super admin",
                }, 400

        user.is_superadmin = new_super_admin_status

    # Handle workspace assignments - simple approach
    if "workspace_ids" in user_data and not user.is_superadmin:
        from enferno.user.models import Membership

        # Clear existing memberships
        db.session.execute(db.delete(Membership).where(Membership.user_id == user.id))

        # Add new memberships
        for workspace_id in user_data.get("workspace_ids", []):
            membership = Membership(
                user_id=user.id, workspace_id=workspace_id, role="member"
            )
            db.session.add(membership)

    db.session.commit()
    # Register activity
    Activity.register(
        current_user.id, "User Update", {"old": old_user_data, "new": user.to_dict()}
    )
    return {"message": "User successfully updated!"}


@bp_user.delete("/api/user/<int:id>")
def api_user_delete(id):
    user = db.get_or_404(User, id)
    # Store user data for activity log before deletion
    user_data = user.to_dict()
    db.session.delete(user)
    db.session.commit()
    # Register activity
    Activity.register(current_user.id, "User Delete", user_data)
    return {"message": "User successfully deleted!"}


@bp_user.get("/activities/")
def activities():
    return render_template("cms/activities.html")


@bp_user.get("/api/activities")
def api_activities():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", PER_PAGE, type=int)

    # Start with base query - newest activities first
    query = db.select(Activity).order_by(Activity.created_at.desc())

    # Paginate results
    pagination = db.paginate(query, page=page, per_page=per_page)

    # Convert activities to dictionaries
    items = []
    for activity in pagination.items:
        # Get user info if available
        user = db.session.get(User, activity.user_id)
        username = user.username if user else f"User ID: {activity.user_id}"

        items.append(
            {
                "id": activity.id,
                "user": username,
                "action": activity.action,
                "data": activity.data,
                "created_at": activity.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    # Create consistent response structure with metadata
    response_data = {
        "items": items,
        "total": pagination.total,
        "perPage": pagination.per_page,
    }

    return Response(json.dumps(response_data), content_type="application/json")
