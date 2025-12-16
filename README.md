# Enferno 🔥

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**[Live Demo](https://demo.enferno.io/)** · **Stop configuring. Start shipping.**

~~Webpack~~ ~~Vite~~ ~~node_modules~~ ~~npm install~~ — Just Python.

```bash
git clone git@github.com:level09/enferno.git && cd enferno
./setup.sh                    # Installs deps + generates secure .env
uv run flask create-db        # Setup database
uv run flask install          # Create admin user
uv run flask run              # → http://localhost:5000
```


https://github.com/user-attachments/assets/a87bfad2-45dc-4d94-bdf1-0448dfea8084



Why Enferno?
===========
- **Zero build step** - Vue 3 + Vuetify 3 run directly in browser. Delete your `node_modules`
- **Auth that works** - 2FA, WebAuthn, OAuth (Google/GitHub) — not a tutorial, actual production code
- **SQLite by default** - Deploy anywhere. ~~Managed database~~ not required
- **AI-native** - Ships with Claude Code & Cursor rules. Your AI already knows the codebase
- **Complexity is opt-in** - Redis, Celery, PostgreSQL when *you* decide, not when the framework demands

> **Want payments?** → **[ReadyKit](https://readykit.dev)** adds Stripe, multi-tenancy, teams on top of Enferno

What's Included
---------------
- **Frontend**: Vue 3, Vuetify 3, Axios - no build tools needed
- **Auth**: Login, registration, password recovery, session management
- **2FA**: TOTP authenticator apps (Google Authenticator, Authy, 1Password)
- **WebAuthn**: Passkeys and hardware security keys (YubiKey, Touch ID)
- **Recovery codes**: Backup codes for account recovery
- **OAuth**: Google and GitHub login
- **Database**: SQLAlchemy ORM, migrations ready
- **Patterns**: Data tables, dialogs, notifications - ready to use

### UI Features

- **Collapsible sidebar** - Nested navigation groups with smooth expand/collapse animations
- **Dark mode** - Theme toggle with localStorage persistence, auto-detects system preference
- **Tabler Icons** - 5000+ icons via CDN, no build step
- **Ember color palette** - Fire-inspired theme matching the Enferno brand
- **Polish included** - Card hover effects, smooth scrollbars, styled data tables

Requirements: Python 3.11+ and [uv](https://docs.astral.sh/uv/)

### Background Tasks

When you need Celery for async jobs:

```bash
uv sync --extra full        # Adds Redis + Celery
# Set REDIS_URL, CELERY_BROKER_URL in .env
```

### Sanity Checks

No pytest ceremony - just real code paths:

```bash
uv run python checks.py     # Run before deploying
```

### Docker

Full production stack with one command:

```bash
docker compose up --build   # Redis, PostgreSQL, Nginx, Celery
```

### VPS Deploy

One command to deploy on any Ubuntu VPS (Hetzner, DigitalOcean, etc.):

```bash
curl -sSL https://raw.githubusercontent.com/level09/ignite/main/ignite.sh | sudo DOMAIN=your-domain.com bash
```

Handles Caddy (auto SSL), Python 3.13, Redis, systemd services. See [Ignite](https://github.com/level09/ignite).

Configuration
------------

Environment variables (`.env`):

```bash
SECRET_KEY=your_secret_key
FLASK_APP=run.py
FLASK_DEBUG=1                    # 0 in production

# PostgreSQL (optional - SQLite works by default)
# SQLALCHEMY_DATABASE_URI=postgresql://user:pass@localhost/dbname

# Background tasks (optional)
# REDIS_URL=redis://localhost:6379/1
# CELERY_BROKER_URL=redis://localhost:6379/2
```

Documentation: [docs.enferno.io](https://docs.enferno.io)

License
-------
MIT

