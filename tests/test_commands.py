import sys

from enferno.extensions import db
from enferno.user.models import User


def _roles(app, email):
    with app.app_context():
        user = db.session.execute(db.select(User).filter_by(email=email)).scalar()
        return [r.name for r in user.roles]


def test_add_role_creates_missing_role_and_persists(app, make_user):
    email = make_user("user@example.com")
    runner = app.test_cli_runner()

    declined = runner.invoke(
        args=["add-role", "-e", email, "-r", "editor"], input="n\n"
    )
    assert declined.exit_code == 1
    assert _roles(app, email) == []

    result = runner.invoke(args=["add-role", "-e", email, "-r", "editor"], input="y\n")
    assert result.exit_code == 0, result.output
    assert _roles(app, email) == ["editor"]


def test_add_role_rejects_unknown_user(app):
    result = app.test_cli_runner().invoke(
        args=["add-role", "-e", "nobody@example.com", "-r", "admin"]
    )
    assert result.exit_code == 1
    assert "does not exist" in result.output


def test_mcp_without_extra_explains_how_to_install(app, monkeypatch):
    for name in ["mcp", *[m for m in sys.modules if m.startswith("mcp.")]]:
        monkeypatch.setitem(sys.modules, name, None)
    monkeypatch.delitem(sys.modules, "enferno.agent_mcp", raising=False)
    result = app.test_cli_runner().invoke(args=["mcp"])
    assert result.exit_code == 1
    assert "uv sync --extra dev --extra mcp" in result.output
