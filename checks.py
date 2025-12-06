#!/usr/bin/env python
"""
Quick sanity checks - run before deploying.
No frameworks, no mocking, just real code paths.

Usage:
    uv run python checks.py
    uv run python checks.py -v  # verbose
"""

import sys
import warnings

# Suppress passlib pkg_resources deprecation warning
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")

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
    assert app.config["SESSION_USE_SIGNER"] is True


# =============================================================================
# RUNNER
# =============================================================================


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
    sys.exit(run_checks())
