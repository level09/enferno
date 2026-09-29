#!/usr/bin/env python
"""
Quick sanity checks - run before deploying.
No frameworks, no mocking, just real code paths.

Usage:
    uv run python checks.py
    uv run python checks.py -v  # verbose
"""

import sys

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


@check("Login and logout work")
def check_auth_flow(app):
    import uuid

    from flask_security.utils import hash_password

    from enferno.extensions import db
    from enferno.user.models import Session, User

    # Runs against the configured DB, so the throwaway user is always removed.
    email = f"checks-{uuid.uuid4().hex}@example.com"
    password = uuid.uuid4().hex
    with app.app_context():
        db.session.add(User(email=email, password=hash_password(password), active=True))
        db.session.commit()
    csrf = app.config.get("WTF_CSRF_ENABLED", True)
    app.config["WTF_CSRF_ENABLED"] = False
    try:
        client = app.test_client()
        r = client.post("/login", data={"email": email, "password": password})
        assert r.status_code == 302, f"login returned {r.status_code}"
        assert client.get("/dashboard/").status_code == 200, "dashboard after login"
        r = client.post("/logout")
        assert r.status_code == 302, f"logout returned {r.status_code}"
        assert client.get("/dashboard/").status_code == 302, "dashboard after logout"
    finally:
        app.config["WTF_CSRF_ENABLED"] = csrf
        with app.app_context():
            user = db.session.execute(db.select(User).filter_by(email=email)).scalar()
            db.session.execute(db.delete(Session).where(Session.user_id == user.id))
            db.session.delete(user)
            db.session.commit()


@check("Security config is sane")
def check_security_config(app):
    assert app.config["SECURITY_PASSWORD_LENGTH_MIN"] >= 8
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True


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
