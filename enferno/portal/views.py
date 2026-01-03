from flask_security import auth_required
from quart import Blueprint, render_template

from enferno.user.models import Activity, Role, User

portal = Blueprint("portal", __name__, static_folder="../static")


@portal.before_request
@auth_required("session")
async def before_request():
    pass


@portal.after_request
async def add_header(response):
    response.headers["Cache-Control"] = "public, max-age=10800"
    return response


@portal.route("/dashboard/")
async def dashboard():
    stats = {
        "users": User.query.count(),
        "roles": Role.query.count(),
        "activities": Activity.query.count(),
    }
    return await render_template("dashboard.html", stats=stats)
