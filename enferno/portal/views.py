from quart import Blueprint, render_template
from quart_security import auth_required
from sqlalchemy import func, select

from enferno.extensions import db
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
        "users": db.session.execute(select(func.count(User.id))).scalar(),
        "roles": db.session.execute(select(func.count(Role.id))).scalar(),
        "activities": db.session.execute(select(func.count(Activity.id))).scalar(),
    }
    return await render_template("dashboard.html", stats=stats)
