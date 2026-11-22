import datetime

from flask import Blueprint, current_app, render_template, request, session
from flask_login import user_logged_out
from flask_security import auth_required, current_user, roles_required
from flask_security.recoverable import send_reset_password_instructions
from flask_security.signals import (
    password_changed,
    password_reset,
    tf_profile_changed,
    user_authenticated,
)
from sqlalchemy.orm import selectinload

from enferno.extensions import db
from enferno.user.models import Activity, Role, Session, User
from enferno.utils.tables import table_response

bp_user = Blueprint("users", __name__, static_folder="../static")


@bp_user.before_request
@auth_required("session")
@roles_required("admin")
def before_request():
    pass


@bp_user.route("/users/")
def users():
    roles = Role.query.all()
    roles = [r.to_dict() for r in roles]
    return render_template(
        "cms/users.html",
        roles=roles,
        invites=current_app.config["SECURITY_RECOVERABLE"],
    )


@bp_user.route("/api/users")
def api_user():
    # to_dict() reads roles, so load them in one query instead of one per user
    query = db.select(User).options(selectinload(User.roles)).order_by(User.id)
    return table_response(
        query,
        sortable={
            "id": User.id,
            "name": User.name,
            "email": User.email,
            "last_login": User.current_login_at,
        },
        searchable=(User.name, User.email),
    )


@bp_user.post("/api/user/")
def api_user_create():
    user_data = request.json.get("item", {})
    invite = not user_data.get("password")
    if invite and not current_app.config["SECURITY_RECOVERABLE"]:
        return {"message": "Set a password, or configure mail to send invites"}, 400
    user = User()
    user.from_dict(user_data)
    if invite:
        # The invited user sets their own password from the emailed reset link
        user.password = User.random_password()
        user.password_set = False
    user.confirmed_at = datetime.datetime.now()
    db.session.add(user)
    try:
        db.session.flush()
        # Activity.register commits the user and its audit entry together
        Activity.register(current_user.id, "User Create", user.to_dict())
    except Exception:
        db.session.rollback()
        return {"message": "Error creating user"}, 400
    if not invite:
        return {"message": "User successfully created!"}
    try:
        send_reset_password_instructions(user)
    except Exception:
        current_app.logger.exception("Invite email to %s failed", user.email)
        # The user exists, so report success: retrying the create would fail
        return {
            "message": "User created, but the invite email failed. Check the mail settings."
        }
    return {"message": f"Invite sent to {user.email}"}


@bp_user.post("/api/user/<int:id>")
def api_user_update(id):
    user = db.get_or_404(User, id)
    user_data = request.json.get("item", {})
    # Store old user data for activity log
    old_user_data = user.to_dict()
    user.from_dict(user_data)
    # Activity.register commits the change and its audit entry together
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
    # Activity.register commits the deletion and its audit entry together
    Activity.register(current_user.id, "User Delete", user_data)
    return {"message": "User successfully deleted!"}


@bp_user.route("/roles/")
def roles():
    return render_template("cms/roles.html")


@bp_user.route("/api/roles", methods=["GET"])
def api_roles():
    return table_response(
        db.select(Role).order_by(Role.id),
        sortable={"id": Role.id, "name": Role.name},
        searchable=(Role.name, Role.description),
    )


@bp_user.route("/api/role/", methods=["POST"])
def api_role_create():
    role_data = request.json.get("item", {})
    role = Role()
    role.from_dict(role_data)
    db.session.add(role)
    try:
        db.session.flush()
        # Activity.register commits the role and its audit entry together
        Activity.register(current_user.id, "Role Create", role.to_dict())
        return {"message": "Role successfully created!"}
    except Exception:
        db.session.rollback()
        return {"message": "Error creating role"}, 400


@bp_user.post("/api/role/<int:id>")
def api_role_update(id):
    role = db.get_or_404(Role, id)
    # Store old role data for activity log
    old_role_data = role.to_dict()
    role_data = request.json.get("item", {})
    role.from_dict(role_data)
    # Activity.register commits the change and its audit entry together
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
    # Activity.register commits the deletion and its audit entry together
    Activity.register(current_user.id, "Role Delete", role_data)
    return {"message": "Role successfully deleted!"}


@bp_user.route("/activities/")
def activities():
    return render_template("cms/activities.html")


@bp_user.route("/api/activities")
def api_activities():
    def serialize(activities):
        # One query for the page's users; activities outlive deleted users
        user_ids = {activity.user_id for activity in activities}
        users = db.session.execute(db.select(User).where(User.id.in_(user_ids)))
        users_by_id = {user.id: user for user in users.scalars()}
        return [
            {
                "id": activity.id,
                "user": users_by_id[activity.user_id].display_name
                if activity.user_id in users_by_id
                else f"User ID: {activity.user_id}",
                "action": activity.action,
                "data": activity.data,
                "created_at": activity.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for activity in activities
        ]

    return table_response(
        db.select(Activity).order_by(Activity.created_at.desc()),
        sortable={"action": Activity.action, "created_at": Activity.created_at},
        searchable=(Activity.action,),
        serialize=serialize,
    )


# --- Flask-Security Signal Handlers ---


@user_authenticated.connect
def user_authenticated_handler(app, user, authn_via, **extra_args):
    """Handle user authentication - create session record and check for new IP."""
    # On registration the new user is logged in before its row is flushed
    if user.id is None:
        db.session.flush()

    # A pre-login session id may have been planted by an attacker.
    current_app.session_interface.regenerate(session)

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

    login = {"ip": user.current_login_ip, "method": authn_via}
    if user.last_login_ip and user.current_login_ip != user.last_login_ip:
        login["previous_ip"] = user.last_login_ip  # first login from this IP
    Activity.register(user.id, "Login", login)

    # Enforce single session if configured
    if current_app.config.get("DISABLE_MULTIPLE_SESSIONS", False):
        user.logout_other_sessions(session_data["session_token"])


@password_changed.connect
def after_password_change(sender, user, **extra_args):
    """Log password change and mark password as user-set."""
    user.password_set = True
    db.session.add(user)
    Activity.register(user.id, "Password Changed", {"email": user.email})


@password_reset.connect
def after_password_reset(sender, user, **extra_args):
    """A reset password is one the user knows, including an invited user's first."""
    user.password_set = True
    db.session.add(user)


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
    """Record the logout and clear the session."""
    Activity.register(user.id, "Logout", {"ip": request.remote_addr})
    if hasattr(session, "sid"):
        # Deactivate the session record
        Session.query.filter_by(session_token=session.sid, is_active=True).update(
            {"is_active": False}
        )
        db.session.commit()
    # Flask-Login deletes the remember cookie only if its "clear" flag survives this.
    remember = session.get("_remember")
    session.clear()
    if remember:
        session["_remember"] = remember
