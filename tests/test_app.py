import re

import pytest

from enferno.extensions import db
from enferno.user.models import Activity, User


def _guarded_urls(app, blueprints=("users", "portal")):
    """One concrete GET or DELETE URL per protected route, ids filled with 1."""
    for rule in app.url_map.iter_rules():
        if rule.endpoint.split(".")[0] not in blueprints or "static" in rule.endpoint:
            continue
        method = next(m for m in ("GET", "POST", "DELETE") if m in rule.methods)
        yield method, rule.rule.replace("<int:id>", "1")


@pytest.mark.parametrize("path", ["/", "/login", "/robots.txt", "/llms.txt"])
def test_public_pages_load(app, path):
    assert app.test_client().get(path).status_code == 200


def test_every_protected_route_rejects_anonymous_users(app):
    client = app.test_client()
    urls = list(_guarded_urls(app))
    assert urls
    for method, url in urls:
        status = client.open(url, method=method).status_code
        assert status in (302, 401), f"{method} {url} returned {status}"


def test_every_admin_route_rejects_non_admins(app, make_user, login):
    client = login(make_user("member@example.com"))
    assert client.get("/dashboard/").status_code == 200
    for method, url in _guarded_urls(app, blueprints=("users",)):
        status = client.open(url, method=method).status_code
        assert status == 403, f"{method} {url} returned {status}"


def test_login_and_post_only_logout(app, make_user, login):
    client = login(make_user("user@example.com"))
    assert client.get("/dashboard/").status_code == 200
    assert client.get("/logout").status_code == 405
    assert client.post("/logout").status_code == 302
    assert client.get("/dashboard/").status_code == 302


def test_wrong_password_is_rejected(app, make_user):
    email = make_user("user@example.com")
    client = app.test_client()
    client.post("/login", data={"email": email, "password": "wrong password!"})
    assert client.get("/dashboard/").status_code == 302


def test_admin_pages_render(admin_client):
    for path in ("/users/", "/roles/", "/activities/"):
        assert admin_client.get(path).status_code == 200, path


def test_admin_user_crud_is_audited(app, admin_client):
    item = {"email": "new@example.com", "password": "another long password"}
    assert admin_client.post("/api/user/", json={"item": item}).status_code == 200
    with app.app_context():
        stmt = db.select(User.id).filter_by(email=item["email"])
        user_id = db.session.execute(stmt).scalar()

    assert (
        admin_client.post(
            f"/api/user/{user_id}", json={"item": {"name": "Renamed"}}
        ).status_code
        == 200
    )
    listing = admin_client.get("/api/users").json
    assert {"items", "total", "perPage"} <= listing.keys()
    assert "Renamed" in [u["name"] for u in listing["items"]]

    assert admin_client.delete(f"/api/user/{user_id}").status_code == 200
    with app.app_context():
        actions = db.session.execute(db.select(Activity.action)).scalars().all()
    assert actions == ["User Create", "User Update", "User Delete"]

    log = admin_client.get("/api/activities").json
    assert log["total"] == 3
    assert {entry["user"] for entry in log["items"]} == {"admin@example.com"}


def test_admin_api_enforces_csrf_token(app, admin_client):
    page = admin_client.get("/roles/").get_data(as_text=True)
    token = re.search(r'X-CSRFToken"\] = "([^"]+)"', page).group(1)
    item = {"item": {"name": "editor"}}
    app.config["WTF_CSRF_ENABLED"] = True
    try:
        rejected = admin_client.post("/api/role/", json=item)
        accepted = admin_client.post(
            "/api/role/", json=item, headers={"X-CSRFToken": token}
        )
    finally:
        app.config["WTF_CSRF_ENABLED"] = False
    assert rejected.status_code == 400
    assert accepted.status_code == 200


def test_security_defaults(app):
    assert app.config["SECURITY_PASSWORD_LENGTH_MIN"] >= 12
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
