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
