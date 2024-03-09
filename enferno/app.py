# -*- coding: utf-8 -*-
import inspect

import click
from flask import Flask, render_template
from enferno.settings import Config
from flask_security import Security, SQLAlchemyUserDatastore
from enferno.user.models import User, Role, WebAuthn
from enferno.user.forms import ExtendedRegisterForm
from enferno.extensions import cache, db, mail, debug_toolbar, session, babel, openai
from enferno.public.views import public
from enferno.user.views import bp_user
from enferno.portal.views import portal
import enferno.commands as commands


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    register_blueprints(app)
    register_extensions(app)

    register_errorhandlers(app)
    register_shellcontext(app)
    register_commands(app, commands)
    return app

def get_locale():
    return 'en'

def register_extensions(app):
    cache.init_app(app)
    db.init_app(app)
    user_datastore = SQLAlchemyUserDatastore(db, User, Role, webauthn_model=WebAuthn)
    security = Security(app, user_datastore,  register_form=ExtendedRegisterForm)
    mail.init_app(app)
    debug_toolbar.init_app(app)
    session.init_app(app)
    babel.init_app(app)
    openai.init_app(app)
    return None


def register_blueprints(app):

    app.register_blueprint(bp_user)
    app.register_blueprint(public)
    app.register_blueprint(portal)
    return None


def register_errorhandlers(app):
    def render_error(error):
        error_code = getattr(error, 'code', 500)
        return render_template("{0}.html".format(error_code)), error_code

    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None


def register_shellcontext(app):
    """Register shell context objects."""

    def shell_context():
        """Shell context objects."""
        return {
            'db': db,
            'User': User,
            'Role': Role
        }

    app.shell_context_processor(shell_context)


def register_commands(app: Flask, commands_module):
    """
    Automatically register all Click commands in the given module.

    Args:
    - app: Flask application instance to register commands to.
    - commands_module: The module containing Click commands.
    """
    for name, obj in inspect.getmembers(commands_module):
        if isinstance(obj, click.Command):
            app.cli.add_command(obj)
