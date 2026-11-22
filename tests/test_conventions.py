"""AGENTS.md hard rules that a scan can check. Each failure names the file, the
line, the fix and where the rule is explained, so an agent can act on it."""

import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
DOCS = "AGENTS.md#hard-rules"

# (pattern, fix); every rule is explained in DOCS
RULES = [
    (
        r"\bmdi-[a-z0-9-]+",
        "use a Tabler icon (ti-*); mdi-* renders blank",
    ),
    (
        r"\btext-(h[1-6]|body-[12]|subtitle-[12]|caption|overline)\b",
        "use the Vuetify 4 type classes (text-headline-small, text-body-medium, "
        "text-body-small); Vuetify 3 names render unstyled",
    ),
    (
        r"<v-row\b[^>]*\s:?(align|justify)=",
        'align rows with classes (class="align-center"), not props',
    ),
    (
        r"href=[\"'][^\"']*logout",
        "log out with a form that POSTs to /logout; GET returns 405",
    ),
]


def _frontend_files():
    yield from (ROOT / "enferno/templates").rglob("*.html")
    yield from (ROOT / "enferno/static/js/components").rglob("*.js")
    yield ROOT / "enferno/static/js/config.js"
    yield ROOT / "enferno/static/js/navigation.js"


def test_frontend_follows_hard_rules():
    problems = []
    for path in _frontend_files():
        lines = path.read_text().splitlines()
        for number, line in enumerate(lines, 1):
            for pattern, fix in RULES:
                if match := re.search(pattern, line):
                    where = f"{path.relative_to(ROOT)}:{number}"
                    problems.append(f"{where}: {match.group(0)!r}: {fix} (see {DOCS})")
    assert not problems, "\n" + "\n".join(problems)


def test_postgres_driver_is_psycopg3():
    for name in ("pyproject.toml", "uv.lock"):
        assert "psycopg2" not in (ROOT / name).read_text(), (
            f"{name}: use psycopg 3, not psycopg2 (see AGENTS.md, Hard rules)"
        )


def test_cloaked_pages_mount_vue():
    """Both layouts hide content until Vue mounts (v-cloak). layout.html mounts a
    default app in its js block; a page that overrides the block, or any page on
    login-layout.html, must mount its own or it renders blank."""
    for path in (ROOT / "enferno/templates").rglob("*.html"):
        text = path.read_text()
        on_login_layout = re.search(r"extends ['\"]login-layout.html", text)
        overrides_js = (
            re.search(r"extends ['\"]layout.html", text) and "{% block js %}" in text
        )
        if on_login_layout or overrides_js:
            assert ".mount(" in text, f"{path.relative_to(ROOT)}: mount a Vue app"
