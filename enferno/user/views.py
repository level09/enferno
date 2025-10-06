import datetime

import orjson as json
from flask import Blueprint, Response, abort, jsonify, render_template, request
from flask_security import auth_required, current_user

from enferno.extensions import db
from enferno.user.models import Activity, Membership, User, Workspace

bp_user = Blueprint("users", __name__, static_folder="../static")

PER_PAGE = 25


def validate_super_admin_change(user, new_status):
    """Validate super admin status changes - enforce single super admin rule"""
    # Trying to add super admin
    if new_status and not user.is_superadmin:
        existing = db.session.execute(
            db.select(User).where(User.is_superadmin)
        ).scalar_one_or_none()
        if existing:
            return (
                "Only one super admin is allowed. Use CLI command to create additional super admins if needed.",
                400,
            )

    # Trying to remove super admin
    if not new_status and user.is_superadmin:
        count = db.session.execute(
            db.select(db.func.count(User.id)).where(User.is_superadmin)
        ).scalar()
        if count <= 1:
            return (
                "Cannot remove the last super admin. Create another super admin first.",
                400,
            )

    return None


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

    query = db.select(User)
    pagination = db.paginate(query, page=page, per_page=per_page)

    def user_with_workspaces(user):
        """Add workspace info to user dict"""
        workspaces = user.get_workspaces()
        return {
            **user.to_dict(),
            "workspace_count": len(workspaces),
            "workspaces": [
                {"id": w.id, "name": w.name, "role": user.get_workspace_role(w.id)}
                for w in workspaces[:3]  # Show first 3
            ],
        }

    items = [user_with_workspaces(user) for user in pagination.items]

    return Response(
        json.dumps(
            {"items": items, "total": pagination.total, "perPage": pagination.per_page}
        ),
        content_type="application/json",
    )


@bp_user.post("/api/user/")
def api_user_create():
    user_data = request.get_json(silent=True) or {}
    user_data = user_data.get("item", {})

    user = User()
    user.from_dict(user_data)

    # Validate super admin changes
    if "is_superadmin" in user_data and user_data["is_superadmin"]:
        error = validate_super_admin_change(user, True)
        if error:
            return jsonify({"error": error[0]}), error[1]
        user.is_superadmin = True

    user.confirmed_at = datetime.datetime.now()
    db.session.add(user)
    db.session.flush()

    # Handle workspace assignments
    if "workspace_ids" in user_data and not user.is_superadmin:
        for workspace_id in user_data.get("workspace_ids", []):
            db.session.add(
                Membership(user_id=user.id, workspace_id=workspace_id, role="member")
            )

    try:
        db.session.commit()
        Activity.register(current_user.id, "User Create", user.to_dict())
        return jsonify({"message": "User successfully created!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@bp_user.post("/api/user/<int:id>")
def api_user_update(id):
    user = db.get_or_404(User, id)
    user_data = request.get_json(silent=True) or {}
    user_data = user_data.get("item", {})

    old_user_data = user.to_dict()
    user.from_dict(user_data)

    # Validate super admin changes
    if "is_superadmin" in user_data:
        error = validate_super_admin_change(user, user_data["is_superadmin"])
        if error:
            return jsonify({"error": error[0]}), error[1]
        user.is_superadmin = user_data["is_superadmin"]

    # Handle workspace assignments
    if "workspace_ids" in user_data and not user.is_superadmin:
        db.session.execute(db.delete(Membership).where(Membership.user_id == user.id))
        for workspace_id in user_data.get("workspace_ids", []):
            db.session.add(
                Membership(user_id=user.id, workspace_id=workspace_id, role="member")
            )

    try:
        db.session.commit()
        Activity.register(
            current_user.id,
            "User Update",
            {"old": old_user_data, "new": user.to_dict()},
        )
        return jsonify({"message": "User successfully updated!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@bp_user.delete("/api/user/<int:id>")
def api_user_delete(id):
    user = db.get_or_404(User, id)
    user_data = user.to_dict()

    try:
        db.session.delete(user)
        db.session.commit()
        Activity.register(current_user.id, "User Delete", user_data)
        return jsonify({"message": "User successfully deleted!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@bp_user.get("/activities/")
def activities():
    return render_template("cms/activities.html")


@bp_user.get("/api/activities")
def api_activities():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", PER_PAGE, type=int)

    query = db.select(Activity).order_by(Activity.created_at.desc())
    pagination = db.paginate(query, page=page, per_page=per_page)

    def activity_to_dict(activity):
        """Convert activity to dict with user info"""
        user = db.session.get(User, activity.user_id)
        return {
            "id": activity.id,
            "user": user.username if user else f"User ID: {activity.user_id}",
            "action": activity.action,
            "data": activity.data,
            "created_at": activity.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }

    items = [activity_to_dict(activity) for activity in pagination.items]

    return Response(
        json.dumps(
            {"items": items, "total": pagination.total, "perPage": pagination.per_page}
        ),
        content_type="application/json",
    )
