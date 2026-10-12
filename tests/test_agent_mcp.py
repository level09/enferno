import asyncio
import os
import sys
from pathlib import Path

import pytest

mcp = pytest.importorskip("mcp")

from enferno.agent_mcp import build_server  # noqa: E402
from enferno.user.models import Activity  # noqa: E402

ROOT = Path(__file__).parents[1]


async def _call(server, *calls):
    async with mcp.Client(server) as client:
        tools = (await client.list_tools()).tools
        results = [await client.call_tool(name, args) for name, args in calls]
    return tools, [r.structured_content for r in results]


def test_tools_are_read_only_and_reflect_the_app(app, make_user):
    make_user("user@example.com")
    with app.app_context():
        Activity.register(1, "User Update", {"name": "x"})

    tools, (routes, schema, activity) = asyncio.run(
        _call(
            build_server(app),
            ("routes", {}),
            ("schema", {}),
            ("recent_activity", {"limit": 5}),
        )
    )

    assert {t.name for t in tools} == {"routes", "schema", "recent_activity"}
    assert all(t.annotations.read_only_hint for t in tools)
    assert "/login" in {r["rule"] for r in routes["result"]}
    assert schema["tables"]["user"]["rows"] == 1
    assert [a["action"] for a in activity["result"]] == ["User Update"]


def test_flask_mcp_speaks_stdio(tmp_path):
    """The real command, as an agent launches it, answers over stdio."""
    env = {
        "PATH": os.environ["PATH"],
        "FLASK_APP": "run.py",
        "SECRET_KEY": "test-secret-key",
        "SECURITY_PASSWORD_SALT": "test-password-salt",
        "SECURITY_TOTP_SECRETS": "test-totp-secret",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'mcp.db'}",
    }
    params = mcp.StdioServerParameters(
        command=sys.executable, args=["-m", "flask", "mcp"], env=env, cwd=ROOT
    )
    _, (routes,) = asyncio.run(_call(params, ("routes", {})))
    assert "/dashboard/" in {r["rule"] for r in routes["result"]}


@pytest.mark.parametrize("limit", [-1, 0, 101])
def test_recent_activity_rejects_out_of_range_limit(app, limit):
    async def call():
        async with mcp.Client(build_server(app)) as client:
            return await client.call_tool("recent_activity", {"limit": limit})

    assert asyncio.run(call()).is_error
