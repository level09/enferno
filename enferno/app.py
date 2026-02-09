import inspect

import click
import quart_flask_patch  # noqa: F401 - Required for flask-babel and flask-sqlalchemy
from quart import Quart, render_template
from quart_security import Security, SQLAlchemyUserDatastore

import enferno.commands as commands
from enferno.extensions import babel, db, session
from enferno.portal.views import portal
from enferno.public.views import public
from enferno.settings import Config
from enferno.user.forms import ExtendedRegisterForm, OAuthAwareChangePasswordForm
from enferno.user.models import Role, User, WebAuthn
from enferno.user.views import bp_user
from enferno.websocket import ws_bp


def create_app(config_object=Config):
    app = Quart(__name__)
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
    db.init_app(app)
    user_datastore = SQLAlchemyUserDatastore(db, User, Role, webauthn_model=WebAuthn)
    Security(
        app,
        user_datastore,
        register_form=ExtendedRegisterForm,
        change_password_form=OAuthAwareChangePasswordForm,
    )

    # Session initialization
    if app.config.get("SESSION_TYPE") == "redis":
        session.init_app(app)
    # For non-redis, fall back to Quart's built-in cookie sessions

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
    app.register_blueprint(ws_bp)
    return None


def register_errorhandlers(app):
    async def render_error(error):
        error_code = getattr(error, "code", 500)
        return await render_template(f"{error_code}.html"), error_code

    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None


def register_shellcontext(app):
    """Register shell context objects."""

    def shell_context():
        """Shell context objects."""
        return {"db": db, "User": User, "Role": Role}

    app.shell_context_processor(shell_context)


def register_commands(app: Quart, commands_module):
    """Automatically register all Click commands and command groups."""
    for _name, obj in inspect.getmembers(commands_module):
        if isinstance(obj, click.Command | click.Group):
            app.cli.add_command(obj)
