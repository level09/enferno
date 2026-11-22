import re

import pytest
from flask import render_template, session
from sqlalchemy.exc import IntegrityError

from enferno.extensions import db, mail
from enferno.user.models import Activity, Role, User

# Every route is protected unless listed here. A new blueprint or route is
# tested automatically; making one public is an explicit, reviewable edit.
PUBLIC_BLUEPRINTS = {"public", "security", "google", "github"}
# Routes any logged-in user may open; every other protected route is admin-only.
MEMBER_ENDPOINTS = {
    "portal.dashboard",
    "portal.sessions",
    "portal.api_sessions",
    "portal.sign_out_other_sessions",
}


def _guarded_urls(app, admin_only=False):
    """Every method of every protected route, URL parameters filled with 1."""
    for rule in app.url_map.iter_rules():
        if rule.endpoint.split(".")[0] in PUBLIC_BLUEPRINTS:
            continue
        if rule.endpoint.split(".")[-1] == "static":
            continue
        if admin_only and rule.endpoint in MEMBER_ENDPOINTS:
            continue
        url = re.sub(r"<[^>]+>", "1", rule.rule)
        for method in sorted(rule.methods - {"HEAD", "OPTIONS"}):
            yield method, url


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
    for method, url in _guarded_urls(app, admin_only=True):
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


def test_register_logs_the_new_user_in(app):
    client = app.test_client()
    response = client.post(
        "/register",
        data={
            "email": "new@example.com",
            "password": "correct horse battery staple",
            "password_confirm": "correct horse battery staple",
        },
    )
    assert response.status_code == 302, response.status_code
    assert client.get("/dashboard/").status_code == 200


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
    assert actions == ["Login", "User Create", "User Update", "User Delete"]

    log = admin_client.get("/api/activities").json
    assert log["total"] == 4
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


def test_failed_audit_rolls_back_the_change(app, admin_client, monkeypatch):
    """A change and its audit entry are saved together or not at all."""
    register = Activity.register.__func__

    def failing_register(cls, user_id, action, data=None):
        return register(cls, user_id, None, data)  # action is NOT NULL

    monkeypatch.setattr(Activity, "register", classmethod(failing_register))
    item = {"item": {"email": "new@example.com", "password": "another long password"}}
    assert admin_client.post("/api/user/", json=item).status_code == 400
    with pytest.raises(IntegrityError):
        admin_client.post("/api/user/1", json={"item": {"name": "Renamed"}})

    with app.app_context():
        emails = db.session.execute(db.select(User.email)).scalars().all()
        assert emails == ["admin@example.com"]
        assert db.session.get(User, 1).name is None
        actions = db.session.execute(db.select(Activity.action)).scalars().all()
        assert actions == ["Login"]  # the admin's own login, nothing from the edits


def test_api_errors_are_json(app, admin_client):
    missing = admin_client.get("/api/user/999")
    assert missing.status_code == 405 and missing.is_json
    gone = admin_client.delete("/api/user/999")
    assert gone.status_code == 404 and gone.json["message"]
    assert not admin_client.get("/no-such-page").is_json

    app.config["WTF_CSRF_ENABLED"] = True
    try:
        rejected = admin_client.post("/api/role/", json={"item": {"name": "x"}})
    finally:
        app.config["WTF_CSRF_ENABLED"] = False
    assert rejected.status_code == 400
    assert "CSRF" in rejected.json["message"]


def test_user_list_query_count_does_not_grow_with_users(app, admin_client):
    def queries_for_listing():
        statements = []
        with app.app_context():
            engine = db.engine
        listen = db.event.listen
        record = lambda *args: statements.append(args[2])  # noqa: E731
        listen(engine, "before_cursor_execute", record)
        try:
            assert admin_client.get("/api/users").status_code == 200
        finally:
            db.event.remove(engine, "before_cursor_execute", record)
        return len(statements)

    few = queries_for_listing()
    with app.app_context():
        role = Role(name="editor")
        for n in range(5):
            db.session.add(User(email=f"u{n}@example.com", password="x", roles=[role]))
        db.session.commit()
    assert queries_for_listing() == few


def test_lists_sort_and_search(admin_client, make_user):
    for email in ("carol@example.com", "bob@example.com"):
        make_user(email)

    def emails(query):
        return [
            u["email"] for u in admin_client.get(f"/api/users?{query}").json["items"]
        ]

    assert emails("sort_by=email") == sorted(emails(""))
    assert emails("sort_by=email&sort_desc=true")[0] == "carol@example.com"
    assert emails("q=BOB") == ["bob@example.com"]
    # Unknown columns are ignored, never passed to SQL
    assert len(emails("sort_by=password")) == 3
    assert admin_client.get("/api/roles?q=adm").json["total"] == 1
    assert admin_client.get("/api/activities?sort_by=action").status_code == 200


def test_invite_emails_a_link_to_set_a_password(app, admin_client):
    with mail.record_messages() as outbox:
        response = admin_client.post(
            "/api/user/", json={"item": {"email": "new@example.com", "active": True}}
        )
    assert response.status_code == 200, response.json
    assert response.json["message"] == "Invite sent to new@example.com"
    assert [m.recipients for m in outbox] == [["new@example.com"]]
    link = re.search(r"http://localhost(/reset/[^\s\"<]+)", outbox[0].body).group(1)

    with app.app_context():
        assert (
            db.session.execute(
                db.select(User.password_set).filter_by(email="new@example.com")
            ).scalar()
            is False
        )

    invited = app.test_client()
    password = "a password I chose myself"
    reset = invited.post(
        link, data={"password": password, "password_confirm": password}
    )
    assert reset.status_code == 302, reset.status_code
    with app.app_context():
        user = db.session.execute(db.select(User).filter_by(email="new@example.com"))
        assert user.scalar_one().password_set is True
    login = app.test_client().post(
        "/login", data={"email": "new@example.com", "password": password}
    )
    assert login.status_code == 302


def test_invite_without_mail_asks_for_a_password(app, admin_client):
    app.config["SECURITY_RECOVERABLE"] = False
    try:
        response = admin_client.post(
            "/api/user/", json={"item": {"email": "x@example.com"}}
        )
    finally:
        app.config["SECURITY_RECOVERABLE"] = True
    assert response.status_code == 400
    assert "password" in response.json["message"]


def test_empty_password_keeps_the_current_one(app, admin_client, login):
    item = {"name": "Admin", "password": ""}
    assert admin_client.post("/api/user/1", json={"item": item}).status_code == 200
    login("admin@example.com")  # asserts the old password still works


def test_sign_out_other_sessions(app, make_user, login):
    email = make_user("user@example.com")
    here, elsewhere = login(email), login(email)

    listed = here.get("/api/sessions").json["items"]
    assert len(listed) == 2
    assert [s["current"] for s in listed].count(True) == 1
    assert "session_token" not in listed[0]

    assert here.post("/api/sessions/sign-out-others").status_code == 200
    assert elsewhere.get("/dashboard/").status_code == 302
    assert here.get("/dashboard/").status_code == 200
    assert len(here.get("/api/sessions").json["items"]) == 1
    with app.app_context():
        actions = db.session.execute(db.select(Activity.action)).scalars().all()
    assert "Signed Out Other Sessions" in actions


def test_error_pages_mount_the_layout(app):
    """Error pages have no Vue app of their own; the layout's default mounts one."""
    with app.test_request_context():
        page = render_template("500.html")
    assert "v-cloak" in page and ".mount('#app')" in page


def test_revoking_another_users_sessions_keeps_the_callers_session(app, make_user):
    make_user("admin@example.com", "admin")
    make_user("member@example.com")
    with app.test_request_context():
        admin = db.session.execute(db.select(User).filter_by(email="admin@example.com"))
        admin = admin.scalar_one()
        session["_user_id"] = admin.fs_uniquifier
        member = db.session.execute(
            db.select(User).filter_by(email="member@example.com")
        )
        member.scalar_one().logout_other_sessions()
        assert session["_user_id"] == admin.fs_uniquifier


def test_admin_set_password_voids_invite_link(app, admin_client):
    with mail.record_messages() as outbox:
        item = {"email": "new@example.com", "active": True}
        admin_client.post("/api/user/", json={"item": item})
    link = re.search(r"http://localhost(/reset/[^\s\"<]+)", outbox[0].body).group(1)
    with app.app_context():
        user_id = db.session.execute(
            db.select(User.id).filter_by(email="new@example.com")
        ).scalar()

    item = {"password": "the admin chose this one"}
    assert (
        admin_client.post(f"/api/user/{user_id}", json={"item": item}).status_code
        == 200
    )
    with app.app_context():
        assert db.session.get(User, user_id).password_set is True
    stolen = "someone else's password"
    app.test_client().post(link, data={"password": stolen, "password_confirm": stolen})
    login = app.test_client().post(
        "/login", data={"email": "new@example.com", "password": stolen}
    )
    assert login.status_code != 302
    # The admin changing their own password stays signed in
    own = {"password": "a brand new admin password"}
    assert admin_client.post("/api/user/1", json={"item": own}).status_code == 200
    assert admin_client.get("/users/").status_code == 200


def test_failed_audit_keeps_other_sessions_signed_in(
    app, make_user, login, monkeypatch
):
    email = make_user("user@example.com")
    here, elsewhere = login(email), login(email)
    register = Activity.register.__func__
    monkeypatch.setattr(
        Activity,
        "register",
        classmethod(
            lambda cls, user_id, action, data=None: register(cls, user_id, None)
        ),
    )
    with pytest.raises(IntegrityError):
        here.post("/api/sessions/sign-out-others")
    assert elsewhere.get("/dashboard/").status_code == 200


def test_invite_mail_failure_still_reports_the_created_user(
    app, admin_client, monkeypatch
):
    def broken_mail(user):
        raise ConnectionRefusedError("SMTP down")

    monkeypatch.setattr(
        "enferno.user.views.send_reset_password_instructions", broken_mail
    )
    response = admin_client.post(
        "/api/user/", json={"item": {"email": "new@example.com"}}
    )
    assert response.status_code == 200
    assert "invite email failed" in response.json["message"]


def test_api_errors_keep_their_headers(admin_client):
    response = admin_client.get("/api/user/999")
    assert response.status_code == 405 and response.is_json
    assert "DELETE" in response.headers["Allow"]


def test_login_and_logout_are_logged(app, make_user, login):
    client = login(make_user("user@example.com"))
    client.post("/logout")
    with app.app_context():
        rows = db.session.execute(db.select(Activity).order_by(Activity.id)).scalars()
        logged = [(a.action, a.data.get("method")) for a in rows]
    assert logged == [("Login", ["password"]), ("Logout", None)]
