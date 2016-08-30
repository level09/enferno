# -*- coding: utf-8 -*-

from flask import Flask, render_template
from settings import ProdConfig
from flask_security import Security, SQLAlchemyUserDatastore
from user.models import User, Role
from user.forms import ExtendedRegisterForm
from extensions import (
    cache,
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

    @app.before_first_request
    def before_first_request():
        db.create_all()
            
    return app



def register_extensions(app):
    cache.init_app(app)
    db.init_app(app)
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security = Security(app, user_datastore, confirm_register_form=ExtendedRegisterForm)
    mail.init_app(app)
    debug_toolbar.init_app(app)

    return None


def register_blueprints(app):
    app.register_blueprint(bp_public)
    app.register_blueprint(bp_user)            
    return None



def register_errorhandlers(app):
    def render_error(error):
        error_code = getattr(error, 'code', 500)
        return render_template("{0}.html".format(error_code)), error_code

    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None