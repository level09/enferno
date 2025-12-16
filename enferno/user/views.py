import datetime

import orjson as json
from flask import Blueprint, Response, current_app, render_template, request, session
from flask_login import user_logged_out
from flask_security import auth_required, current_user, roles_required
from flask_security.signals import (
    password_changed,
    tf_profile_changed,
    user_authenticated,
)

from enferno.extensions import db
from enferno.user.models import Activity, Role, Session, User

bp_user = Blueprint("users", __name__, static_folder="../static")

PER_PAGE = 25


@bp_user.before_request
@auth_required("session")
@roles_required("admin")
def before_request():
    pass


@bp_user.route("/users/")
def users():
    roles = Role.query.all()
    roles = [r.to_dict() for r in roles]
    return render_template("cms/users.html", roles=roles)


@bp_user.route("/api/users")
def api_user():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", PER_PAGE, type=int)

    # Start with base query - this pattern makes it easy to add filters later
    query = db.select(User)

    # Paginate results
    pagination = db.paginate(query, page=page, per_page=per_page)

    # Convert users to dictionaries
    items = [user.to_dict() for user in pagination.items]

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
    user.from_dict(user_data)  # Assuming from_dict is correctly implemented
    user.confirmed_at = datetime.datetime.now()
    db.session.add(user)
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
    db.session.commit()
    # Register activity
    Activity.register(
        current_user.id, "User Update", {"old": old_user_data, "new": user.to_dict()}
    )
    return {"message": "User successfully updated!"}


@bp_user.route("/api/user/<int:id>", methods=["DELETE"])
def api_user_delete(id):
    user = db.get_or_404(User, id)
    # Store user data for activity log before deletion
    user_data = user.to_dict()
    db.session.delete(user)
    db.session.commit()
    # Register activity
    Activity.register(current_user.id, "User Delete", user_data)
    return {"message": "User successfully deleted!"}


@bp_user.route("/roles/")
def roles():
    return render_template("cms/roles.html")


@bp_user.route("/api/roles", methods=["GET"])
def api_roles():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", PER_PAGE, type=int)

    # Start with base query
    query = db.select(Role)

    # Paginate results
    pagination = db.paginate(query, page=page, per_page=per_page)

    # Convert roles to dictionaries
    items = [role.to_dict() for role in pagination.items]

    # Create consistent response structure
    response_data = {
        "items": items,
        "total": pagination.total,
        "perPage": pagination.per_page,
    }

    return Response(json.dumps(response_data), content_type="application/json")


@bp_user.route("/api/role/", methods=["POST"])
def api_role_create():
    role_data = request.json.get("item", {})
    role = Role()
    role.from_dict(role_data)
    db.session.add(role)
    try:
        db.session.commit()
        # Register activity
        Activity.register(current_user.id, "Role Create", role.to_dict())
        return {"message": "Role successfully created!"}
    except Exception as e:
        db.session.rollback()
        return {"message": "Error creating role", "error": str(e)}, 412


@bp_user.post("/api/role/<int:id>")
def api_role_update(id):
    role = db.get_or_404(Role, id)
    # Store old role data for activity log
    old_role_data = role.to_dict()
    role_data = request.json.get("item", {})
    role.from_dict(role_data)
    db.session.commit()
    # Register activity
    Activity.register(
        current_user.id, "Role Update", {"old": old_role_data, "new": role.to_dict()}
    )
    return {"message": "Role successfully updated!"}


@bp_user.route("/api/role/<int:id>", methods=["DELETE"])
def api_role_delete(id):
    role = db.get_or_404(Role, id)
    # Store role data for activity log before deletion
    role_data = role.to_dict()
    db.session.delete(role)
    db.session.commit()
    # Register activity
    Activity.register(current_user.id, "Role Delete", role_data)
    return {"message": "Role successfully deleted!"}


@bp_user.route("/activities/")
def activities():
    return render_template("cms/activities.html")


@bp_user.route("/api/activities")
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

        items.append(
            {
                "id": activity.id,
                "user": user.display_name if user else f"User ID: {activity.user_id}",
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


# --- Flask-Security Signal Handlers ---


@user_authenticated.connect
def user_authenticated_handler(app, user, authn_via, **extra_args):
    """Handle user authentication - create session record and check for new IP."""
    session_data = {
        "user_id": user.id,
        "session_token": session.sid if hasattr(session, "sid") else str(id(session)),
        "ip_address": request.remote_addr,
        "meta": {
            "browser": request.user_agent.browser,
            "browser_version": request.user_agent.version,
            "os": request.user_agent.platform,
            "device": request.user_agent.string,
        },
    }

    # Create session record
    Session.create_session(**session_data)

    # Log if logged in from a different IP
    if user.last_login_ip and user.current_login_ip != user.last_login_ip:
        Activity.register(
            user.id,
            "Login from new IP",
            {"old_ip": user.last_login_ip, "new_ip": user.current_login_ip},
        )

    # Enforce single session if configured
    if current_app.config.get("DISABLE_MULTIPLE_SESSIONS", False):
        user.logout_other_sessions(session_data["session_token"])


@password_changed.connect
def after_password_change(sender, user, **extra_args):
    """Log password change and mark password as user-set."""
    user.password_set = True
    db.session.add(user)
    Activity.register(user.id, "Password Changed", {"email": user.email})


@tf_profile_changed.connect
def after_tf_profile_change(sender, user, **extra_args):
    """Log 2FA profile changes."""
    Activity.register(
        user.id,
        "Two-Factor Profile Changed",
        {"email": user.email, "method": user.tf_primary_method},
    )


@user_logged_out.connect
def user_logged_out_handler(app, user, **extra_args):
    """Clear session on logout."""
    if hasattr(session, "sid"):
        # Deactivate the session record
        Session.query.filter_by(session_token=session.sid, is_active=True).update(
            {"is_active": False}
        )
        db.session.commit()
    session.clear()
