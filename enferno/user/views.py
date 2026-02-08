import datetime

import orjson as json
from quart import Blueprint, Response, current_app, render_template, request, session
from quart_security import (
    auth_required,
    current_user,
    password_changed,
    roles_required,
    tf_profile_changed,
    user_authenticated,
    user_logged_out,
)
from sqlalchemy import select

from enferno.extensions import db
from enferno.user.models import Activity, Role, Session, User

bp_user = Blueprint("users", __name__, static_folder="../static")

PER_PAGE = 25


@bp_user.before_request
@auth_required("session")
@roles_required("admin")
async def before_request():
    pass


@bp_user.route("/users/")
async def users():
    roles = db.session.execute(select(Role)).scalars().all()
    roles = [r.to_dict() for r in roles]
    return await render_template("cms/users.html", roles=roles)


@bp_user.route("/api/users")
async def api_user():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", PER_PAGE, type=int)

    query = db.select(User)
    pagination = db.paginate(query, page=page, per_page=per_page)
    items = [user.to_dict() for user in pagination.items]

    response_data = {
        "items": items,
        "total": pagination.total,
        "perPage": pagination.per_page,
    }

    return Response(json.dumps(response_data), content_type="application/json")


@bp_user.post("/api/user/")
async def api_user_create():
    json_data = await request.json
    user_data = json_data.get("item", {})
    user = User()
    user.from_dict(user_data)
    user.confirmed_at = datetime.datetime.now()
    db.session.add(user)
    try:
        db.session.commit()
        Activity.register(current_user.id, "User Create", user.to_dict())
        return {"message": "User successfully created!"}
    except Exception as e:
        db.session.rollback()
        return {"message": "Error creating user", "error": str(e)}, 412


@bp_user.post("/api/user/<int:id>")
async def api_user_update(id):
    user = db.get_or_404(User, id)
    json_data = await request.json
    user_data = json_data.get("item", {})
    old_user_data = user.to_dict()
    user.from_dict(user_data)
    db.session.commit()
    Activity.register(
        current_user.id, "User Update", {"old": old_user_data, "new": user.to_dict()}
    )
    return {"message": "User successfully updated!"}


@bp_user.route("/api/user/<int:id>", methods=["DELETE"])
async def api_user_delete(id):
    user = db.get_or_404(User, id)
    user_data = user.to_dict()
    db.session.delete(user)
    db.session.commit()
    Activity.register(current_user.id, "User Delete", user_data)
    return {"message": "User successfully deleted!"}


@bp_user.route("/roles/")
async def roles():
    return await render_template("cms/roles.html")


@bp_user.route("/api/roles", methods=["GET"])
async def api_roles():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", PER_PAGE, type=int)

    query = db.select(Role)
    pagination = db.paginate(query, page=page, per_page=per_page)
    items = [role.to_dict() for role in pagination.items]

    response_data = {
        "items": items,
        "total": pagination.total,
        "perPage": pagination.per_page,
    }

    return Response(json.dumps(response_data), content_type="application/json")


@bp_user.route("/api/role/", methods=["POST"])
async def api_role_create():
    json_data = await request.json
    role_data = json_data.get("item", {})
    role = Role()
    role.from_dict(role_data)
    db.session.add(role)
    try:
        db.session.commit()
        Activity.register(current_user.id, "Role Create", role.to_dict())
        return {"message": "Role successfully created!"}
    except Exception as e:
        db.session.rollback()
        return {"message": "Error creating role", "error": str(e)}, 412


@bp_user.post("/api/role/<int:id>")
async def api_role_update(id):
    role = db.get_or_404(Role, id)
    old_role_data = role.to_dict()
    json_data = await request.json
    role_data = json_data.get("item", {})
    role.from_dict(role_data)
    db.session.commit()
    Activity.register(
        current_user.id, "Role Update", {"old": old_role_data, "new": role.to_dict()}
    )
    return {"message": "Role successfully updated!"}


@bp_user.route("/api/role/<int:id>", methods=["DELETE"])
async def api_role_delete(id):
    role = db.get_or_404(Role, id)
    role_data = role.to_dict()
    db.session.delete(role)
    db.session.commit()
    Activity.register(current_user.id, "Role Delete", role_data)
    return {"message": "Role successfully deleted!"}


@bp_user.route("/activities/")
async def activities():
    return await render_template("cms/activities.html")


@bp_user.route("/api/activities")
async def api_activities():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", PER_PAGE, type=int)

    query = db.select(Activity).order_by(Activity.created_at.desc())
    pagination = db.paginate(query, page=page, per_page=per_page)

    items = []
    for activity in pagination.items:
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

    response_data = {
        "items": items,
        "total": pagination.total,
        "perPage": pagination.per_page,
    }

    return Response(json.dumps(response_data), content_type="application/json")


# --- Signal Handlers ---


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

    Session.create_session(**session_data)

    if user.last_login_ip and user.current_login_ip != user.last_login_ip:
        Activity.register(
            user.id,
            "Login from new IP",
            {"old_ip": user.last_login_ip, "new_ip": user.current_login_ip},
        )

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
        stmt = (
            Session.__table__.update()
            .where(Session.session_token == session.sid)
            .where(Session.is_active == True)  # noqa: E712
            .values(is_active=False)
        )
        db.session.execute(stmt)
        db.session.commit()
    session.clear()
