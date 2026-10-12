# Changelog

## v13.3.0 (2026-10-12)

### Upgrade notes for existing apps
- CSRF is enforced on every POST, PUT and DELETE. Plain HTML forms in your own templates need `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`; axios on `layout.html` pages sends the token automatically.
- `checks.py` is gone; run `uv run pytest` instead. Point `TEST_DATABASE_URI` only at a disposable database, because the suite drops every table.
- Run `uv sync` to pick up Flask-Security-Too 5.9.1.

### Security
- Require Flask-Security-Too 5.9.1, which fixes an open redirect (GHSA-ccgp-pv8r-95wm). Other dependencies upgraded, including SQLAlchemy 2.1.4.
- Enable CSRF protection for the whole app. The admin JSON API accepted POST and DELETE requests without a token; only Flask-Security's own forms were protected. Axios now sends the token automatically on `layout.html` pages, and the logout forms include it.

### Fixed
- The activity log API crashed once any activity existed: it unpacked `(activity, user)` pairs from `db.paginate()`, which returns activities only. It now loads the page's users in one query.
- `flask add-role` never saved the role, crashed when the role was missing, and could not create it. It now commits, and offers to create a missing role.
- `migrations/env.py` used `get_engine()`, which Flask-SQLAlchemy 3.2 removes.

### Added
- `flask mcp`: a local, read-only MCP server (stdio) for coding agents, exposing routes, schema with row counts, migration revision and the audit log. Install with `--extra mcp`; `.mcp.json` registers it.
- pytest suite replacing `checks.py`: every protected route rejects anonymous users and non-admins, login and POST-only logout, audited admin CRUD, CSRF on the admin API, a single migration head, models matching migrations, and `setup.sh` modes. `TEST_DATABASE_URI` runs it against PostgreSQL, as CI does.
- `setup.sh --docker`, and setup runs without prompts when there is no terminal (agents, CI). It refuses to overwrite an existing `.env` in that mode.
- `vendor.sh` pins and downloads Vue, Vuetify and axios.
- `/llms.txt`, a starter description of the app for LLM tools, served like `robots.txt`.

### Changed
- Vue 3.5.43, Vuetify 3.13.6 and axios 1.20.0.
- `AGENTS.md` is the single agent guide; removed the stale `.windsurfrules`, which recommended Material Design icons. The docs page `cursor-rules` is now `ai-coding`, with a redirect.
- Move the `enferno-dev` skill to `.agents/skills/`, the shared location for Codex, Cursor, Copilot, Gemini CLI and others. `.claude/skills` is a symlink to it, and `npx skills add level09/enferno` installs it elsewhere.
- Cut `AGENTS.md` from 1,130 to about 90 lines of stack, layout, commands, routes and hard rules; code patterns live only in the skill. Removed the unused `templates/core/` scaffolding templates, left over from the old OpenAI generator. Fixed skill examples that missed the `auth_required` import and mounted pages without `layoutMixin`.

## v13.2.0 (2026-09-29)

### Upgrade notes for existing apps
- Logout is POST-only in Flask-Security 5.9. Replace any `href="/logout"` links in your own templates with a form that posts to `/logout`.
- `psycopg2-binary` is replaced by `psycopg` 3. Run `uv sync`; `postgresql://` URLs keep working.
- Databases created before migrations existed: run `uv run flask db stamp head` once.

### Added
- Alembic migrations via Flask-Migrate, with a baseline revision. `flask create-db` stamps new databases automatically.
- PostgreSQL smoke checks on Python 3.11 to 3.14 and a production container build in CI.

### Security
- Upgrade Flask-Security-Too to 5.9.0, which fixes GHSA-f66q-9rf6-8795 (WebAuthn reauthentication freshness bypass). Logout is now POST-only; templates submit a form instead of linking to `/logout`.
- Replace deprecated `bleach` with `nh3`, now required by Flask-Security for WebAuthn.
- Stop publishing PostgreSQL and Redis container ports and require explicit database and Redis passwords.
- Update vendored Vue, Vuetify, and Axios assets to the versions tested in ReadyKit 1.5.1.

Thanks to Ali Tanveer ([@alivirgo](https://github.com/alivirgo)) for privately reporting the shared Docker Compose port and default password issues in ReadyKit.

### Fixed
- Admin pages froze the browser on Vue 3.5: `filterNavByRole` mutated reactive nav items inside a computed property, re-triggering it forever. It now returns copies.
- Vuetify's built-in icons (table sort, pagination, selects, checkboxes) rendered blank because they default to MDI, which the layout never loaded. They are now mapped to Tabler.
- Switch the PostgreSQL driver from `psycopg2-binary` to `psycopg` 3. SQLAlchemy 2.1 resolves `postgresql://` URLs to psycopg 3, so existing URLs work unchanged.
- `checks.py` now logs a throwaway user in and out, catching auth regressions such as the POST-only logout in Flask-Security 5.9.
- Require Python 3.11 or newer in setup and install dependencies with the selected interpreter.
- Install and configure optional Redis sessions and Celery with `./setup.sh --full` or Docker setup.
- Generate Docker Redis settings using `REDIS_URL` and preserve the SQLite default for local setup.
- Check each Celery container through Redis instead of inheriting the image's HTTP health check.
- Install Celery and Redis in the production Docker image. The image synced only the `wsgi` extra while `docker-compose.yml` runs a Celery worker, so `enferno.tasks` always fell back to `CELERY_AVAILABLE = False`.

### Changed
- Upgrade all dependencies, including SQLAlchemy 2.1, Flask-Security-Too 5.9 and oauthlib 4.0.
- Build the production image on Python 3.13 and add Python 3.14 to the CI matrix.
- Vendor Tabler Icons 3.48.0 (woff2 only) instead of loading `@latest` from a CDN, and remove the unused 5 MB Material Design Icons bundle.
- Removed the passlib, flask-script, speaklater, six, mako, python-editor, pycparser, cffi and bcrypt pins. Flask-Security-Too supplies the `passlib` namespace through libpass, so the explicit passlib 1.7.4 pin was shadowing it.
- Dropped the `setuptools<82` pin, which only existed for passlib 1.7.4's use of `pkg_resources`, and the warning suppression that went with it.
- Dropped the kombu, amqp and vine pins from the `full` extra; Celery pulls them in.
- Raised the cryptography floor to 50.0.0.
- Removed `enferno.__version__`. Nothing read it and it had drifted to 12.0.0 while `pyproject.toml` said 13.2.0, which is now the single source of truth.
- Replaced the deprecated `CACHE_TYPE = "simple"` with the full backend path, dropped `SESSION_USE_SIGNER` (deprecated in Flask-Session and removed in its next minor release), and moved to `RegisterFormV2`.

## v11.3.0 (2025-12-02)

### Added
- Lite mode: Zero-config startup with `uv sync && flask run` — no Redis required
- Full mode: Optional Redis + Celery via `uv sync --extra full`
- SQLAlchemy-based sessions as default (Redis sessions optional)
- AI-assisted development with AGENTS.md for Claude Code and Cursor

### Changed
- Upgrade all dependencies, including SQLAlchemy 2.1, Flask-Security-Too 5.9 and oauthlib 4.0.
- Redis and Celery moved to optional dependencies
- SQLite database path now uses absolute path in `instance/enferno.db`
- Updated documentation for lite/full mode workflow
- Simplified README with clearer positioning

## v11.2.0 (2025-04-24)

### Added
- Production-ready Docker configuration with multi-stage builds
- PostgreSQL service in Docker Compose setup
- Improved environment variable handling for Docker
- Support for user-specific Docker UID configuration
- Enhanced setup.sh script with Docker configuration option

### Changed
- Upgrade all dependencies, including SQLAlchemy 2.1, Flask-Security-Too 5.9 and oauthlib 4.0.
- Optimized Dockerfile with multi-stage build for smaller, more secure images
- Fixed Redis connectivity by using correct environment variables
- Improved nginx configuration with proper retry settings
- Enhanced tmpfs configuration for better performance
- Added proper health checks for all Docker services

## v11.1.0 (2025-03-30)

### Added
- Migrated from pip/venv to uv for package management
- Faster installation and dependency resolution
- Better Python environment isolation

### Changed
- Upgrade all dependencies, including SQLAlchemy 2.1, Flask-Security-Too 5.9 and oauthlib 4.0.
- Updated setup.sh script to use uv instead of venv
- Modified Dockerfile to use uv for package installation
- Updated documentation to reference uv

## v11.0 (2023-03-27)

### Added
- New activity model to track user actions like creating and editing users/roles
- Cursor Rules for improved code generation and assistance
- Comprehensive documentation for Cursor Rules approach

### Changed
- Upgrade all dependencies, including SQLAlchemy 2.1, Flask-Security-Too 5.9 and oauthlib 4.0.
- Improved user and roles tables design in both frontend and backend
- Transitioned from OpenAI integration to Cursor Rules for code generation
- Enhanced admin user creation with better console output

### Removed
- Removed flask-openai dependency and related code generation commands
- Removed OpenAI API key requirements

### Fixed
- Various UI and UX improvements
- Code cleanup and bug fixes 