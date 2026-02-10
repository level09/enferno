#!/usr/bin/env python
"""
Quick sanity checks - run before deploying.
No frameworks, no mocking, just real code paths.

Usage:
    uv run python checks.py
    uv run python checks.py -v  # verbose
"""

import asyncio
import sys

VERBOSE = "-v" in sys.argv
PASSED = 0
FAILED = 0


def check(name):
    """Decorator to register a check"""

    def decorator(f):
        async def wrapper(app):
            global PASSED, FAILED
            try:
                result = f(app)
                if asyncio.iscoroutine(result):
                    await result
                PASSED += 1
                print(f"  \033[32m✓\033[0m {name}")
                return True
            except Exception as e:
                FAILED += 1
                print(f"  \033[31m✗\033[0m {name}")
                if VERBOSE:
                    print(f"    → {e}")
                return False

        wrapper._check_name = name
        return wrapper

    return decorator


# =============================================================================
# CHECKS
# =============================================================================


@check("App boots without errors")
def check_app_boots(app):
    assert app is not None
    assert app.config["SECRET_KEY"]


@check("Database connection works")
async def check_database(app):
    import enferno.extensions as ext

    async with ext.engine.connect() as conn:
        from sqlalchemy import text

        await conn.execute(text("SELECT 1"))


@check("User model queryable")
async def check_user_model(app):
    from sqlalchemy import select

    import enferno.extensions as ext
    from enferno.user.models import User

    async with ext.async_session_factory() as session:
        await session.execute(select(User).limit(1))


@check("Role model queryable")
async def check_role_model(app):
    from sqlalchemy import select

    import enferno.extensions as ext
    from enferno.user.models import Role

    async with ext.async_session_factory() as session:
        await session.execute(select(Role).limit(1))


@check("All blueprints register")
def check_blueprints(app):
    blueprints = list(app.blueprints.keys())
    required = ["users", "public", "portal", "security", "ws"]
    for bp in required:
        assert bp in blueprints, f"Missing blueprint: {bp}"


@check("Critical routes exist")
def check_routes(app):
    rules = [r.rule for r in app.url_map.iter_rules()]

    critical_routes = [
        "/",
        "/login",
        "/dashboard/",
        "/ws",
    ]
    for route in critical_routes:
        assert route in rules, f"Missing route: {route}"


@check("Security config is sane")
def check_security_config(app):
    assert app.config["SECURITY_PASSWORD_LENGTH_MIN"] >= 8
    assert app.config["SESSION_USE_SIGNER"] is True


@check("Async session factory initialized")
def check_session_factory(app):
    import enferno.extensions as ext

    assert ext.engine is not None, "Engine not initialized"
    assert ext.async_session_factory is not None, "Session factory not initialized"


@check("All models queryable")
async def check_all_models(app):
    from sqlalchemy import select

    import enferno.extensions as ext
    from enferno.user.models import Activity, OAuth, Session, WebAuthn

    async with ext.async_session_factory() as session:
        for model in [Activity, Session, OAuth, WebAuthn]:
            await session.execute(select(model).limit(1))


@check("Admin routes exist")
def check_admin_routes(app):
    rules = [r.rule for r in app.url_map.iter_rules()]
    admin_routes = [
        "/users/",
        "/roles/",
        "/activities/",
        "/api/users",
        "/api/roles",
        "/api/activities",
    ]
    for route in admin_routes:
        assert route in rules, f"Missing admin route: {route}"


@check("Auth routes exist")
def check_auth_routes(app):
    rules = [r.rule for r in app.url_map.iter_rules()]
    auth_routes = ["/login", "/register", "/logout", "/change"]
    for route in auth_routes:
        assert route in rules, f"Missing auth route: {route}"


@check("WebAuthn enabled")
def check_webauthn(app):
    assert app.config.get("SECURITY_WEBAUTHN") is True
    assert app.config.get("SECURITY_WAN_ALLOW_AS_FIRST_FACTOR") is True


@check("2FA enabled")
def check_two_factor(app):
    assert app.config.get("SECURITY_TWO_FACTOR") is True
    assert "authenticator" in app.config.get("SECURITY_TWO_FACTOR_ENABLED_METHODS", [])


@check("Background tasks module loads")
def check_tasks_module(app):
    from enferno.tasks import run_in_background

    assert callable(run_in_background)


@check("WebSocket module loads")
def check_websocket_module(app):
    from enferno.websocket import broadcast, get_connected_users

    assert callable(broadcast)
    assert callable(get_connected_users)


@check("No Celery dependency")
def check_no_celery(app):
    import importlib.util

    assert importlib.util.find_spec("celery") is None, "Celery should not be installed"


@check("Templates exist")
def check_templates(app):
    import os

    template_dir = os.path.join(app.root_path, "templates")
    required = [
        "layout.html",
        "dashboard.html",
        "index.html",
        "401.html",
        "404.html",
        "500.html",
        "cms/users.html",
        "cms/roles.html",
        "cms/activities.html",
    ]
    for tpl in required:
        path = os.path.join(template_dir, tpl)
        assert os.path.exists(path), f"Missing template: {tpl}"


@check("Static assets exist")
def check_static_assets(app):
    import os

    static_dir = os.path.join(app.root_path, "static")
    required = [
        "js/vue.min.js",
        "js/vuetify.min.js",
        "js/config.js",
        "js/navigation.js",
        "js/components/index.js",
        "css/vuetify.min.css",
        "css/layout.css",
        "css/app.css",
    ]
    for asset in required:
        path = os.path.join(static_dir, asset)
        assert os.path.exists(path), f"Missing static asset: {asset}"


@check("GET / returns 200")
async def check_http_index(app):
    client = app.test_client()
    response = await client.get("/")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"


@check("GET /dashboard/ requires auth")
async def check_auth_redirect(app):
    client = app.test_client()
    response = await client.get("/dashboard/")
    assert response.status_code in (302, 401), (
        f"Expected 302/401, got {response.status_code}"
    )


@check("GET /api/users requires auth")
async def check_api_requires_auth(app):
    client = app.test_client()
    response = await client.get("/api/users")
    assert response.status_code in (302, 401), (
        f"Expected 302/401, got {response.status_code}"
    )


@check("CLI commands registered")
def check_cli_commands(app):
    commands = list(app.cli.commands.keys())
    required = ["create-db", "install", "create", "add-role", "reset"]
    for cmd in required:
        assert cmd in commands, f"Missing CLI command: {cmd}"


# =============================================================================
# RUNNER
# =============================================================================


async def run_checks():
    from enferno.app import create_app

    print("\n\033[1mRunning checks...\033[0m\n")

    app = create_app()
    checks = [v for v in globals().values() if hasattr(v, "_check_name")]

    for check_fn in checks:
        await check_fn(app)

    print()
    if FAILED == 0:
        print(f"\033[32m\033[1m✓ All {PASSED} checks passed\033[0m\n")
        return 0
    else:
        print(f"\033[31m\033[1m✗ {FAILED}/{PASSED + FAILED} checks failed\033[0m\n")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(run_checks()))
