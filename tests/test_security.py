from types import SimpleNamespace
from unittest.mock import patch

from conftest import PASSWORD
from flask import session
from flask_security import current_user

from enferno.extensions import db
from enferno.public.views import oauth_logged_in
from enferno.user.models import OAuth, User

GOOGLE = SimpleNamespace(name="google")
TOKEN = {"access_token": "token"}


def _oauth_callback(app, **claims):
    data = {"id": "google-1", "email": "user@example.com", "email_verified": True}
    with (
        app.test_request_context("/login/google/authorized"),
        patch(
            "enferno.public.views.get_oauth_user_data",
            return_value=data | claims,
        ),
    ):
        response = oauth_logged_in(GOOGLE, TOKEN)
        return response, current_user.is_authenticated, dict(session)


def test_oauth_never_links_an_existing_email(app, make_user):
    make_user("user@example.com")
    response, authenticated, _ = _oauth_callback(app)
    assert response.location == "/login"
    assert not authenticated

    rejected, authenticated, _ = _oauth_callback(
        app, email="new@example.com", email_verified=False
    )
    assert rejected is False
    assert not authenticated
    with app.app_context():
        assert db.session.execute(db.select(OAuth)).first() is None
        assert db.session.execute(db.select(db.func.count(User.id))).scalar() == 1


def test_oauth_login_requires_enrolled_2fa(app, make_user):
    make_user("user@example.com")
    with app.app_context():
        user = db.session.execute(db.select(User)).scalar_one()
        user.tf_primary_method = "authenticator"
        user.tf_totp_secret = "secret"
        db.session.add(
            OAuth(
                provider="google", provider_user_id="google-1", token=TOKEN, user=user
            )
        )
        db.session.commit()

    response, authenticated, state = _oauth_callback(app)
    assert response.location.startswith("/tf-validate")
    assert not authenticated
    assert "_user_id" not in state and state["tf_user_id"]


def test_login_rotates_session_id(app, make_user):
    make_user("user@example.com")
    attacker = app.test_client()
    attacker.get("/login")
    planted = attacker.get_cookie("session").value

    victim = app.test_client()
    victim.set_cookie("session", planted)
    victim.post("/login", data={"email": "user@example.com", "password": PASSWORD})

    assert victim.get_cookie("session").value != planted
    assert attacker.get("/dashboard/").status_code == 302


def test_empty_roles_revokes_admin(app, admin_client):
    with app.app_context():
        admin_id = db.session.execute(db.select(User.id)).scalar_one()
    response = admin_client.post(f"/api/user/{admin_id}", json={"item": {"roles": []}})
    assert response.status_code == 200
    assert admin_client.get("/api/users").status_code == 403


def test_single_session_signs_out_previous_session(app, make_user, login):
    make_user("user@example.com")
    app.config["DISABLE_MULTIPLE_SESSIONS"] = True
    try:
        first = login("user@example.com")
        second = login("user@example.com")
    finally:
        app.config["DISABLE_MULTIPLE_SESSIONS"] = False
    assert first.get("/dashboard/").status_code == 302
    assert second.get("/dashboard/").status_code == 200
