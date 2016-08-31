# -*- coding: utf-8 -*-

from flask import Flask, render_template
from settings import ProdConfig
from flask_security import Security, MongoEngineUserDatastore
from user.models import User, Role
from admin.views import UserView, RoleView
from user.forms import ExtendedRegisterForm
from extensions import (
    cache,
    admin,
    db,
    mail,
    debug_toolbar,
)
from public.views import bp_public
from user.views import bp_user
import warnings
from flask.exthook import ExtDeprecationWarning


def create_app(config_object=ProdConfig):
    warnings.simplefilter('ignore', ExtDeprecationWarning)
    app = Flask(__name__)
    app.config.from_object(config_object)
    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)
    return app


def register_extensions(app):
    cache.init_app(app)
    db.init_app(app)
    admin.init_app(app)
    register_admin_views(admin)
    user_datastore = MongoEngineUserDatastore(db, User, Role)
    security = Security(app, user_datastore, confirm_register_form=ExtendedRegisterForm)
    mail.init_app(app)
    debug_toolbar.init_app(app)

    return None


def register_blueprints(app):
    app.register_blueprint(bp_public)
    app.register_blueprint(bp_user)
    return None

def register_admin_views(admin):
    admin.add_view(UserView(User))
    admin.add_view(RoleView(Role))
    return None


def register_errorhandlers(app):
    def render_error(error):
        error_code = getattr(error, 'code', 500)
        return render_template("{0}.html".format(error_code)), error_code

    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None