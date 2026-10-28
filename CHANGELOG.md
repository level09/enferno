# Changelog

## Unreleased

### Security
- Vendored axios 1.21.0, Vue 3.5.44, Vuetify 4.3.1 and Tabler icons 3.50.0, now fetched by `./vendor.sh`. Tabler ships its font as subsets in `static/tabler/fonts/`, so pages load only the icon groups they use.
- Werkzeug's minimum is 3.1.9 (PYSEC-2026-4312), and the locked dependencies, including dev tools, are updated (flask-security-too 5.9.2, sqlalchemy 2.1.6, wtforms 3.3.1, python-dateutil 3.0.0).
- CI audits the locked dependencies for known vulnerabilities with `uv audit`.

## v14.1.0 (2026-10-21)

### Upgrade notes for existing apps
- Google and GitHub sign-in no longer links to an existing account with the same email. Users who registered with a password sign in with it; accounts already linked keep working.
- OAuth sign-in requires an email the provider has verified. For GitHub that is the primary verified address.
- Sending `"roles": []` when updating a user now removes all roles instead of leaving them unchanged.

### Security
- OAuth sign-in goes through two-factor authentication when the user has it enabled.
- The session id is replaced on every login, so a session id planted before login cannot be reused.
- With `DISABLE_MULTIPLE_SESSIONS`, a new login now signs out other sessions and remember-me cookies. Before, it only marked their tracking rows inactive.

### Fixed
- Registering a new account returned a 500 (#74).
- `.env-sample` uses `apikey` as the SendGrid SMTP username (#75).

### Added
- `MAIL_PORT`, `MAIL_USE_SSL` and `MAIL_USE_TLS` are read from the environment. The default stays port 465 with SSL (#73).

## v14.0.0 (2026-10-15)

### Upgrade notes for existing apps
- Vuetify 4 replaces Vuetify 3; the vendored files come with the update. Check your own templates:
  - Typography classes moved to Material Design 3 names. `text-h4` becomes `text-headline-large`, `text-h5` becomes `text-headline-small`, `text-h6` becomes `text-title-large`, `text-subtitle-1` and `text-body-1` become `text-body-large`, `text-body-2` becomes `text-body-medium`, `text-caption` becomes `text-body-small`. The old classes no longer exist and render unstyled.
  - Use classes for row alignment: `<v-row class="align-center justify-center">` instead of the `align` and `justify` props.
  - Vuetify's CSS now lives in cascade layers, so any CSS outside a layer beats every Vuetify style. Element rules such as `a { color: ... }` in your own stylesheets will recolor buttons and list items; scope them to your own classes or put them in `@layer vuetify-core.reset`.
  - Buttons are no longer uppercase by default, elevation goes up to 5 instead of 24, and `v-container` max widths are smaller. A `fill-height` container no longer centers its content vertically; add `d-flex align-center`.
- `layout.html` now mounts Vue on `<div id="app">` with `<v-app>` inside it. Pages that extend `layout.html` and wrap their content in their own `<v-app id="app">` must drop that wrapper.
- The light theme uses darker shades so text and buttons meet WCAG AA contrast: primary `#C2410C`, info `#0369A1`, success `#15803D`, warning `#A16207`. The dark theme puts dark text on its bright buttons, and its error red is `#F87171`.
- The `dark-mode` class on `body` is gone. Target dark mode in CSS with `.v-theme--dark`.

### Fixed
- The page background now follows the theme. `<v-app>` was the Vue mount point, so it never rendered and dark mode showed the browser's grey instead of the theme's slate.
- Between 840 and 1145px wide, the navigation drawer opened as an overlay on every page load and the menu button to reopen it was hidden. The drawer and menu button now share Vuetify's mobile breakpoint, and the drawer starts closed on small screens.
- Edit and delete in the users and roles tables are real buttons with labels, reachable from the keyboard and screen readers. Other icon-only buttons have labels too.
- The flame logo inverts on every dark page, including the login and 2FA screens.
- Flash messages use theme colors; warning text was 1.9:1 on yellow.
- The forgot password, reset password and resend confirmation pages were Vue 2 era templates that broke the layout. They are rebuilt like the 2FA pages and work when `SECURITY_RECOVERABLE` or `SECURITY_CONFIRMABLE` is turned on.

### Removed
- The unused `confirm_email.html` template and the Read the Docs config left over from MkDocs. Docs are on Mintlify.

### Changed
- Vuetify 4.2.4. Dependency lock refreshed.
- `AGENTS.md` and the `enferno-dev` skill describe the Vuetify 4 rules, so coding agents stop writing Vuetify 3 class names.

## v13.3.1 (2026-10-14)

### Fixed
- Rerunning `setup.sh` on an existing `.env` regenerated `SECRET_KEY`, the password salt and the TOTP secrets, which broke every stored password and 2FA enrollment. With `--docker` it also rotated `DB_PASSWORD`, which Postgres only reads when its volume is first created. Setup now keeps all of these, plus `REDIS_PASSWORD`, and moves other edits to the backup.
- `.env` and its backups are created with mode 600 instead of being readable by every user on the machine.
- Added `.flaskenv` so `flask` commands work with a `.env` that doesn't set `FLASK_APP`.

### Upgrade notes
- Tighten an existing `.env`: `chmod 600 .env .env.backup.*`

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