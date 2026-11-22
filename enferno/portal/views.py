from flask import Blueprint, session
from flask.templating import render_template
from flask_security import auth_required, current_user

from enferno.extensions import db
from enferno.user.models import Activity, Role, Session, User

portal = Blueprint("portal", __name__, static_folder="../static")


@portal.before_request
@auth_required("session")
def before_request():
    pass


@portal.route("/dashboard/")
def dashboard():
    stats = {}
    if current_user.has_role("admin"):
        stats = {
            "users": User.query.count(),
            "roles": Role.query.count(),
            "activities": Activity.query.count(),
        }
    return render_template("dashboard.html", stats=stats)


@portal.route("/sessions/")
def sessions():
    return render_template("sessions.html")


@portal.get("/api/sessions")
def api_sessions():
    """The current user's signed-in sessions, newest first."""
    query = (
        db.select(Session)
        .filter_by(user_id=current_user.id, is_active=True)
        .order_by(Session.last_active.desc())
    )
    current = getattr(session, "sid", None)
    return {
        "items": [
            {**row.to_dict(), "current": row.session_token == current}
            for row in db.session.execute(query).scalars()
        ]
    }


@portal.post("/api/sessions/sign-out-others")
def sign_out_other_sessions():
    current_user.logout_other_sessions(getattr(session, "sid", None), commit=False)
    # Activity.register commits the revocation and its audit entry together
    Activity.register(
        current_user.id, "Signed Out Other Sessions", {"email": current_user.email}
    )
    return {"message": "Signed out of every other session"}
