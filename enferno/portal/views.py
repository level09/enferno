from flask import Blueprint
from flask.templating import render_template
from flask_security import auth_required

from enferno.user.models import Activity, Role, User

portal = Blueprint("portal", __name__, static_folder="../static")


@portal.before_request
@auth_required("session")
def before_request():
    pass


@portal.after_request
def add_header(response):
    response.headers["Cache-Control"] = "public, max-age=10800"
    return response


@portal.route("/dashboard/")
def dashboard():
    stats = {
        "users": User.query.count(),
        "roles": Role.query.count(),
        "activities": Activity.query.count(),
    }
    return render_template("dashboard.html", stats=stats)
