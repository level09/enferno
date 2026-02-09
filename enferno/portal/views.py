from quart import Blueprint, g, render_template
from quart_security import auth_required
from sqlalchemy import func, select

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
    users_count = (await g.db_session.execute(select(func.count(User.id)))).scalar()
    roles_count = (await g.db_session.execute(select(func.count(Role.id)))).scalar()
    activities_count = (
        await g.db_session.execute(select(func.count(Activity.id)))
    ).scalar()
    stats = {
        "users": users_count,
        "roles": roles_count,
        "activities": activities_count,
    }
    return await render_template("dashboard.html", stats=stats)
