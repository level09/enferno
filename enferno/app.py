import inspect

import click
from flask import Flask, render_template
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from flask_dance.contrib.github import make_github_blueprint
from flask_dance.contrib.google import make_google_blueprint
from flask_security import Security, SQLAlchemyUserDatastore, current_user

import enferno.commands as commands
from enferno.extensions import babel, cache, db, debug_toolbar, mail, session
from enferno.portal.views import portal
from enferno.public.views import public
from enferno.settings import Config
from enferno.user.forms import ExtendedRegisterForm, OAuthAwareChangePasswordForm
from enferno.user.models import OAuth, Role, User, WebAuthn
from enferno.user.views import bp_user


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    register_blueprints(app)
    register_extensions(app)
    register_errorhandlers(app)
    register_shellcontext(app)
    register_commands(app, commands)
    return app


def locale_selector():
    return "en"


def register_extensions(app):
    cache.init_app(app)
    db.init_app(app)
    user_datastore = SQLAlchemyUserDatastore(db, User, Role, webauthn_model=WebAuthn)
    Security(
        app,
        user_datastore,
        register_form=ExtendedRegisterForm,
        change_password_form=OAuthAwareChangePasswordForm,
    )
    mail.init_app(app)
    debug_toolbar.init_app(app)

    # Session initialization - pass db for SQLAlchemy sessions
    if app.config.get("SESSION_TYPE") == "sqlalchemy":
        app.config["SESSION_SQLALCHEMY"] = db
    session.init_app(app)

    babel.init_app(
        app,
        locale_selector=locale_selector,
        default_domain="messages",
        default_locale="en",
    )

    return None


def register_blueprints(app):
    app.register_blueprint(bp_user)
    app.register_blueprint(public)
    app.register_blueprint(portal)

    # Setup OAuth if enabled
    if app.config.get("GOOGLE_AUTH_ENABLED") and app.config.get(
        "GOOGLE_OAUTH_CLIENT_ID"
    ):
        google_bp = make_google_blueprint(
            client_id=app.config.get("GOOGLE_OAUTH_CLIENT_ID"),
            client_secret=app.config.get("GOOGLE_OAUTH_CLIENT_SECRET"),
            scope=[
                "https://www.googleapis.com/auth/userinfo.profile",
                "https://www.googleapis.com/auth/userinfo.email",
                "openid",
            ],
            reprompt_select_account=False,
        )
        google_bp.storage = SQLAlchemyStorage(OAuth, db.session, user=current_user)
        app.register_blueprint(google_bp, url_prefix="/login")

    if app.config.get("GITHUB_AUTH_ENABLED") and app.config.get(
        "GITHUB_OAUTH_CLIENT_ID"
    ):
        github_bp = make_github_blueprint(
            client_id=app.config.get("GITHUB_OAUTH_CLIENT_ID"),
            client_secret=app.config.get("GITHUB_OAUTH_CLIENT_SECRET"),
            scope=["user:email"],
        )
        github_bp.storage = SQLAlchemyStorage(OAuth, db.session, user=current_user)
        app.register_blueprint(github_bp, url_prefix="/login")

    return None


def register_errorhandlers(app):
    def render_error(error):
        error_code = getattr(error, "code", 500)
        return render_template(f"{error_code}.html"), error_code

    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None


def register_shellcontext(app):
    """Register shell context objects."""

    def shell_context():
        """Shell context objects."""
        return {"db": db, "User": User, "Role": Role}

    app.shell_context_processor(shell_context)


def register_commands(app: Flask, commands_module):
    """
    Automatically register all Click commands and command groups in the given module.

    Args:
    - app: Flask application instance to register commands to.
    - commands_module: The module containing Click commands and command groups.
    """
    for _name, obj in inspect.getmembers(commands_module):
        if isinstance(obj, click.Command | click.Group):
            app.cli.add_command(obj)
