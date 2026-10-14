# AGENTS.md

Guidance for coding agents working on Enferno. Code patterns and full examples live in the `enferno-dev` skill at `.agents/skills/enferno-dev/` (also exposed to Claude Code through `.claude/skills`). Load it before writing features.

## Stack

- **Backend**: Flask 3.1, blueprints, application factory in `enferno/app.py`
- **Database**: SQLAlchemy 2.x (`db.select()`, `db.paginate()`), Alembic via Flask-Migrate. SQLite by default, PostgreSQL through `psycopg` 3
- **Auth**: Flask-Security-Too 5.9 (email login, TOTP 2FA, WebAuthn, recovery codes), Google/GitHub OAuth via Flask-Dance
- **Frontend**: Vue 3 + Vuetify 4 served from `enferno/static/js/`, no build step, Tabler icons vendored in `enferno/static/tabler/`
- **Optional**: Redis sessions and Celery (`uv sync --extra full`); MCP server for agents (`--extra mcp`); uWSGI (`--extra wsgi`)
- **Tooling**: `uv` for everything, Ruff for lint and format

## Layout

```
enferno/
├── app.py            # create_app, blueprint and extension registration
├── settings.py       # Config from environment (.env)
├── extensions.py     # db, migrate, cache, mail, session, babel, debug toolbar
├── commands.py       # Flask CLI commands (auto-registered)
├── public/           # "/" and OAuth handlers, no auth
├── portal/           # "/dashboard/", login required
├── user/             # Admin CMS: users, roles, activities (+ models, forms)
├── tasks/            # Celery app and tasks (celery is None when not configured)
├── utils/base.py     # BaseMixin: save()/delete()
├── static/js/        # vue, vuetify, axios, config.js, navigation.js, components/
└── templates/        # layout.html, cms/, security/
migrations/           # Alembic revisions
tests/                # pytest: routes, auth, admin API, migrations, setup.sh
vendor.sh             # Pinned Vue, Vuetify and axios downloads
.mcp.json             # Registers `flask mcp` with MCP-aware agents
setup.sh              # Venv, deps, .env with generated secrets (--full for Redis/Celery)
```

## Commands

```bash
./setup.sh                             # First-time setup (--full for Redis + Celery, --docker for Compose)
uv run flask create-db                 # Create tables, stamp migrations
uv run flask install                   # Create admin user
uv run flask run --port 5001           # Dev server (5000 is often taken on macOS)
uv run flask db migrate -m "msg"       # Draft a migration; review before applying
uv run flask db upgrade                # Apply migrations
uv run flask create -e <email> -p <password>
uv run flask add-role -e <email> -r <role>
uv run flask reset -e <email> -p <password>
uv run flask i18n extract|init|update|compile
uv run pytest                          # In-memory SQLite; TEST_DATABASE_URI drops all tables
./vendor.sh                            # Re-download vendored JS after bumping its pins
uv run flask mcp                       # Read-only MCP: routes, schema, migration revision, audit log
uv run ruff check --fix . && uv run ruff format .
docker compose up --build              # Postgres, Redis, Celery, nginx (needs DB_PASSWORD, REDIS_PASSWORD)
```

## Routes

| Path | Access |
|------|--------|
| `/` | Public |
| `/dashboard/` | Logged in |
| `/users/`, `/roles/`, `/activities/` | Admin |
| `GET /api/users`, `/api/roles`, `/api/activities` | Admin, `?page=&per_page=` |
| `POST /api/user/`, `/api/role/` | Admin, create |
| `POST /api/user/<id>`, `/api/role/<id>` | Admin, update |
| `DELETE /api/user/<id>`, `/api/role/<id>` | Admin |
| `/login`, `/register`, `/tf-setup`, `/change`, `POST /logout` | Flask-Security |

Lists return `{"items": [...], "total": n, "perPage": n}`. Create and update take `{"item": {...}}`.

## Conventions

- Protect admin blueprints in `before_request` with `@auth_required("session")` and `@roles_required("admin")`.
- Models use `BaseMixin` and implement `to_dict()` / `from_dict()`. Schema changes go through `flask db migrate`, reviewed by hand.
- Log admin actions: `Activity.register(current_user.id, "User Update", {"old": old, "new": new})`.
- Pages extend `layout.html`, mount their own Vue app with `mixins: [layoutMixin]`, call `registerEnfernoComponents(app)`, and use `config.delimiters` (`${ }`). `{{ }}` is Jinja.
- Pass server data to Vue with `<script type="application/json">{{ data|tojson|safe }}</script>`.
- Config comes from `.env`; never hardcode secrets.

## Hard rules

- **Icons**: Tabler only (`ti-*`). Vuetify's built-in icons are mapped to Tabler in `static/js/config.js`; `mdi-*` renders blank.
- **Logout**: POST only. Use a form posting to `/logout`, never a link.
- **CSRF**: every POST/PUT/DELETE is checked (`CSRFProtect`). Axios sends the token automatically on `layout.html` pages; plain HTML forms need `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`.
- **Postgres driver**: `psycopg` 3. Do not add `psycopg2-binary`.
- **Reactivity**: never mutate reactive state inside a computed property; Vue 3.5 loops forever.
- **Vuetify 4**: Material Design 3 classes (`text-headline-small`, `text-body-medium`, `text-body-small`; `text-h5`, `text-body-2` and `text-caption` no longer exist). Align rows with classes (`<v-row class="align-center">`), not `align`/`justify` props. Vuetify's CSS is in cascade layers, so any unlayered rule beats every component style; put element-level rules like `a { }` in `@layer vuetify-core.reset`.
- **Vendored JS**: bump pins in `vendor.sh` and run it, never hand-edit the files. Vue and Vuetify must stay compatible; after updating, load an admin page in a real browser.

## Before committing

1. `uv run ruff check --fix . && uv run ruff format .`
2. `uv run pytest`
3. For UI changes, click through `/dashboard/` and `/users/` as an admin.

## Commits

One-line conventional messages (`fix: ...`, `chore: ...`). Stage files explicitly, never `git add .` or `-A`. No AI mentions.
