import inspect

import click
from quart import Quart, g, render_template, request
from quart_security import Security, SQLAlchemyUserDatastore
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import enferno.commands as commands
import enferno.extensions as ext
from enferno.extensions import session
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


def register_extensions(app):
    # Async SQLAlchemy engine + session factory
    ext.engine = create_async_engine(app.config["SQLALCHEMY_DATABASE_URI"])
    ext.async_session_factory = async_sessionmaker(ext.engine, expire_on_commit=False)

    @app.before_request
    async def _open_session():
        g.db_session = ext.async_session_factory()

    @app.after_request
    async def _close_session(response):
        db_session = g.pop("db_session", None)
        if db_session is not None:
            await db_session.close()
        return response

    user_datastore = SQLAlchemyUserDatastore(
        lambda: g.db_session, User, Role, webauthn_model=WebAuthn
    )
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

    # Rate limit auth endpoints
    from enferno.utils.ratelimit import check_security_rate_limit

    _auth_paths = frozenset({"/login", "/register", "/reset", "/confirm"})

    @app.before_request
    async def _rate_limit_auth():
        if request.path in _auth_paths and request.method == "POST":
            return await check_security_rate_limit()

    return None


def register_blueprints(app):
    app.register_blueprint(bp_user)
    app.register_blueprint(public)
    app.register_blueprint(portal)
    app.register_blueprint(ws_bp)
    return None


def register_errorhandlers(app):
    import logging

    logger = logging.getLogger(__name__)

    def _is_api_request():
        return (
            request.path.startswith("/api/")
            or request.accept_mimetypes.best == "application/json"
        )

    @app.errorhandler(Exception)
    async def handle_exception(error):
        db_session = g.pop("db_session", None)
        if db_session is not None:
            try:
                await db_session.rollback()
            except Exception:
                pass
            finally:
                await db_session.close()

        code = getattr(error, "code", 500)
        if code == 500:
            logger.exception("Unhandled exception")

        if _is_api_request():
            return {"message": "Internal server error"}, code
        return await render_template(f"{code}.html"), code

    async def render_error(error):
        error_code = getattr(error, "code", 500)
        if _is_api_request():
            return {
                "message": error.name if hasattr(error, "name") else "Error"
            }, error_code
        return await render_template(f"{error_code}.html"), error_code

    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None


def register_shellcontext(app):
    """Register shell context objects."""

    def shell_context():
        """Shell context objects."""
        return {"User": User, "Role": Role}

    app.shell_context_processor(shell_context)


def register_commands(app: Quart, commands_module):
    """Automatically register all Click commands and command groups."""
    for _name, obj in inspect.getmembers(commands_module):
        if isinstance(obj, click.Command | click.Group):
            app.cli.add_command(obj)
