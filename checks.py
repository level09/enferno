#!/usr/bin/env python
"""
Quick sanity checks - run before deploying.
No frameworks, no mocking, just real code paths.

Usage:
    uv run python checks.py
    uv run python checks.py -v  # verbose
    uv run python checks.py --config  # offline configuration checks
"""

import argparse
import importlib.util
import os
import sys
from pathlib import Path

VERBOSE = "-v" in sys.argv
PASSED = 0
FAILED = 0


def check(name):
    """Decorator to register a check"""

    def decorator(f):
        def wrapper(app):
            global PASSED, FAILED
            try:
                f(app)
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
def check_database(app):
    from enferno.extensions import db

    with app.app_context():
        db.session.execute(db.text("SELECT 1"))


@check("User model loads")
def check_user_model(app):
    from enferno.user.models import User

    with app.app_context():
        User.query.limit(1).all()


@check("Role model loads")
def check_role_model(app):
    from enferno.user.models import Role

    with app.app_context():
        Role.query.limit(1).all()


@check("All blueprints register")
def check_blueprints(app):
    blueprints = list(app.blueprints.keys())
    required = ["users", "public", "portal"]
    for bp in required:
        assert bp in blueprints, f"Missing blueprint: {bp}"


@check("Critical routes exist")
def check_routes(app):
    rules = [r.rule for r in app.url_map.iter_rules()]

    critical_routes = [
        "/",
        "/login",
        "/dashboard/",
    ]
    for route in critical_routes:
        assert route in rules, f"Missing route: {route}"


@check("Security config is sane")
def check_security_config(app):
    assert app.config["SECURITY_PASSWORD_LENGTH_MIN"] >= 8
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True


# =============================================================================
# RUNNER
# =============================================================================


def check_configuration():
    """Check local settings without booting the app or contacting services."""
    from dotenv import dotenv_values, load_dotenv
    from sqlalchemy import create_engine
    from sqlalchemy.exc import SQLAlchemyError

    root = Path(__file__).resolve().parent
    load_dotenv(root / ".env")
    sample = dotenv_values(root / ".env-sample")
    errors = []

    def require(name, value, action):
        if (
            not value
            or not value.strip()
            or "your_" in value
            or value == sample.get(name)
        ):
            errors.append(f"{name}: missing or placeholder value. {action}")

    for name in ("SECRET_KEY", "SECURITY_PASSWORD_SALT", "SECURITY_TOTP_SECRETS"):
        require(
            name,
            os.environ.get(name),
            "Generate secure values with ./setup.sh for a new install.",
        )

    redis_url = os.environ.get("REDIS_URL") or os.environ.get("REDIS_SESSION")
    broker = os.environ.get("CELERY_BROKER_URL")
    backend = os.environ.get("CELERY_RESULT_BACKEND")
    if backend and not broker:
        errors.append("CELERY_BROKER_URL: required when CELERY_RESULT_BACKEND is set.")
    for package, needed in (
        ("redis", redis_url or broker or backend),
        ("celery", broker or backend),
    ):
        if needed and importlib.util.find_spec(package) is None:
            errors.append(
                f"{package}: configured but not installed. Run uv sync --extra dev --extra full."
            )

    # Config can fail during import; validate its startup requirements first.
    if not errors:
        try:
            from enferno.settings import Config
        except (ValueError, TypeError):
            errors.append(
                "Config could not load. Check REDIS_URL/REDIS_SESSION and Redis URL options."
            )
        else:
            try:
                # Engine construction validates the URL and driver without connecting.
                create_engine(Config.SQLALCHEMY_DATABASE_URI).dispose()
            except (SQLAlchemyError, ValueError, ImportError, TypeError):
                errors.append(
                    "SQLALCHEMY_DATABASE_URI: invalid database URL or unavailable dialect/driver."
                )

            for provider in ("GOOGLE", "GITHUB"):
                if getattr(Config, f"{provider}_AUTH_ENABLED"):
                    for field in ("CLIENT_ID", "CLIENT_SECRET"):
                        name = f"{provider}_OAUTH_{field}"
                        require(
                            name,
                            getattr(Config, name),
                            f"Set it or disable {provider}_AUTH_ENABLED.",
                        )

    for error in errors:
        print(f"FAIL {error}")
    if errors:
        print(f"Configuration checks failed: {len(errors)} issue(s).")
        return 1
    print(
        "Configuration checks passed. Service connectivity and credentials were not verified."
    )
    return 0


def run_checks():
    from enferno.app import create_app

    print("\n\033[1mRunning checks...\033[0m\n")

    app = create_app()
    checks = [v for v in globals().values() if hasattr(v, "_check_name")]

    for check_fn in checks:
        check_fn(app)

    print()
    if FAILED == 0:
        print(f"\033[32m\033[1m✓ All {PASSED} checks passed\033[0m\n")
        return 0
    else:
        print(f"\033[31m\033[1m✗ {FAILED}/{PASSED + FAILED} checks failed\033[0m\n")
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check Enferno configuration or application health."
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show smoke-check errors"
    )
    parser.add_argument(
        "--config", action="store_true", help="Check settings without starting the app"
    )
    args = parser.parse_args()
    VERBOSE = args.verbose
    sys.exit(check_configuration() if args.config else run_checks())
