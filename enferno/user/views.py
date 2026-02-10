import datetime

import orjson as json
from quart import Blueprint, Response, current_app, g, render_template, request, session
from quart_security import (
    auth_required,
    current_user,
    password_changed,
    roles_required,
    tf_profile_changed,
    user_authenticated,
    user_logged_out,
)
from sqlalchemy import func, select

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
    result = await g.db_session.execute(select(Role))
    roles = [r.to_dict() for r in result.scalars().all()]
    return await render_template("cms/users.html", roles=roles)


@bp_user.route("/api/users")
async def api_user():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", PER_PAGE, type=int)

    query = select(User)
    count_result = await g.db_session.execute(select(func.count()).select_from(User))
    total = count_result.scalar()

    result = await g.db_session.execute(
        query.offset((page - 1) * per_page).limit(per_page)
    )
    items = [user.to_dict() for user in result.scalars().all()]

    response_data = {"items": items, "total": total, "perPage": per_page}
    return Response(json.dumps(response_data), content_type="application/json")


@bp_user.post("/api/user/")
async def api_user_create():
    json_data = await request.json
    user_data = json_data.get("item", {})
    user = User()
    await user.from_dict(user_data)
    user.confirmed_at = datetime.datetime.now()
    g.db_session.add(user)
    try:
        await g.db_session.flush()
        await g.db_session.refresh(user, ["roles"])
        await Activity.register(current_user.id, "User Create", user.to_dict())
        await g.db_session.commit()
        return {"message": "User successfully created!"}
    except Exception as e:
        await g.db_session.rollback()
        return {"message": "Error creating user", "error": str(e)}, 412


@bp_user.post("/api/user/<int:id>")
async def api_user_update(id):
    user = await g.db_session.get(User, id)
    if user is None:
        return {"message": "User not found"}, 404
    json_data = await request.json
    user_data = json_data.get("item", {})
    old_user_data = user.to_dict()
    try:
        await user.from_dict(user_data)
        await g.db_session.flush()
        await g.db_session.refresh(user, ["roles"])
        await Activity.register(
            current_user.id,
            "User Update",
            {"old": old_user_data, "new": user.to_dict()},
        )
        await g.db_session.commit()
        return {"message": "User successfully updated!"}
    except Exception as e:
        await g.db_session.rollback()
        return {"message": "Error updating user", "error": str(e)}, 412


@bp_user.route("/api/user/<int:id>", methods=["DELETE"])
async def api_user_delete(id):
    user = await g.db_session.get(User, id)
    if user is None:
        return {"message": "User not found"}, 404
    user_data = user.to_dict()
    try:
        await g.db_session.delete(user)
        await Activity.register(current_user.id, "User Delete", user_data)
        await g.db_session.commit()
        return {"message": "User successfully deleted!"}
    except Exception as e:
        await g.db_session.rollback()
        return {"message": "Error deleting user", "error": str(e)}, 412


@bp_user.route("/roles/")
async def roles():
    return await render_template("cms/roles.html")


@bp_user.route("/api/roles", methods=["GET"])
async def api_roles():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", PER_PAGE, type=int)

    count_result = await g.db_session.execute(select(func.count()).select_from(Role))
    total = count_result.scalar()

    result = await g.db_session.execute(
        select(Role).offset((page - 1) * per_page).limit(per_page)
    )
    items = [role.to_dict() for role in result.scalars().all()]

    response_data = {"items": items, "total": total, "perPage": per_page}
    return Response(json.dumps(response_data), content_type="application/json")


@bp_user.route("/api/role/", methods=["POST"])
async def api_role_create():
    json_data = await request.json
    role_data = json_data.get("item", {})
    role = Role()
    role.from_dict(role_data)
    g.db_session.add(role)
    try:
        await g.db_session.flush()
        await Activity.register(current_user.id, "Role Create", role.to_dict())
        await g.db_session.commit()
        return {"message": "Role successfully created!"}
    except Exception as e:
        await g.db_session.rollback()
        return {"message": "Error creating role", "error": str(e)}, 412


@bp_user.post("/api/role/<int:id>")
async def api_role_update(id):
    role = await g.db_session.get(Role, id)
    if role is None:
        return {"message": "Role not found"}, 404
    old_role_data = role.to_dict()
    json_data = await request.json
    role_data = json_data.get("item", {})
    try:
        role.from_dict(role_data)
        await Activity.register(
            current_user.id,
            "Role Update",
            {"old": old_role_data, "new": role.to_dict()},
        )
        await g.db_session.commit()
        return {"message": "Role successfully updated!"}
    except Exception as e:
        await g.db_session.rollback()
        return {"message": "Error updating role", "error": str(e)}, 412


@bp_user.route("/api/role/<int:id>", methods=["DELETE"])
async def api_role_delete(id):
    role = await g.db_session.get(Role, id)
    if role is None:
        return {"message": "Role not found"}, 404
    role_data = role.to_dict()
    try:
        await g.db_session.delete(role)
        await Activity.register(current_user.id, "Role Delete", role_data)
        await g.db_session.commit()
        return {"message": "Role successfully deleted!"}
    except Exception as e:
        await g.db_session.rollback()
        return {"message": "Error deleting role", "error": str(e)}, 412


@bp_user.route("/activities/")
async def activities():
    return await render_template("cms/activities.html")


@bp_user.route("/api/activities")
async def api_activities():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", PER_PAGE, type=int)

    count_result = await g.db_session.execute(
        select(func.count()).select_from(Activity)
    )
    total = count_result.scalar()

    result = await g.db_session.execute(
        select(Activity, User)
        .outerjoin(User, Activity.user_id == User.id)
        .order_by(Activity.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )

    items = []
    for activity, user in result.all():
        items.append(
            {
                "id": activity.id,
                "user": user.display_name if user else f"User ID: {activity.user_id}",
                "action": activity.action,
                "data": activity.data,
                "created_at": activity.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    response_data = {"items": items, "total": total, "perPage": per_page}
    return Response(json.dumps(response_data), content_type="application/json")


# --- Signal Handlers ---


@user_authenticated.connect
async def user_authenticated_handler(app, user, authn_via, **extra_args):
    """Handle user authentication - create session record and check for new IP."""
    session_data = {
        "user_id": user.id,
        "session_token": getattr(session, "sid", None) or session.get("_id", ""),
        "ip_address": request.remote_addr,
        "meta": {
            "browser": request.user_agent.browser,
            "browser_version": request.user_agent.version,
            "os": request.user_agent.platform,
            "device": request.user_agent.string,
        },
    }

    await Session.create_session(**session_data)
    await g.db_session.commit()

    if user.last_login_ip and user.current_login_ip != user.last_login_ip:
        await Activity.register(
            user.id,
            "Login from new IP",
            {"old_ip": user.last_login_ip, "new_ip": user.current_login_ip},
        )

    if current_app.config.get("DISABLE_MULTIPLE_SESSIONS", False):
        await user.logout_other_sessions(session_data["session_token"])


@password_changed.connect
async def after_password_change(sender, user, **extra_args):
    """Log password change and mark password as user-set."""
    user.password_set = True
    g.db_session.add(user)
    await Activity.register(user.id, "Password Changed", {"email": user.email})


@tf_profile_changed.connect
async def after_tf_profile_change(sender, user, **extra_args):
    """Log 2FA profile changes."""
    await Activity.register(
        user.id,
        "Two-Factor Profile Changed",
        {"email": user.email, "method": user.tf_primary_method},
    )


@user_logged_out.connect
async def user_logged_out_handler(app, user, **extra_args):
    """Clear session on logout."""
    token = getattr(session, "sid", None) or session.get("_id")
    if token:
        stmt = (
            Session.__table__.update()
            .where(Session.session_token == token)
            .where(Session.is_active == True)  # noqa: E712
            .values(is_active=False)
        )
        await g.db_session.execute(stmt)
        await g.db_session.commit()
    session.clear()
