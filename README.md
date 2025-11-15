# Project Enferno

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Enferno is a modern Flask framework optimized for AI-assisted development workflows. By combining carefully crafted development patterns, smart Cursor Rules, and modern libraries, it enables developers to build sophisticated web applications with unprecedented speed. Whether you're using AI-powered IDEs like Cursor or traditional tools, Enferno's intelligent patterns and contextual guides help you create production-ready SAAS applications faster than ever.

> **Looking for a production-ready SaaS starter?** → Check out **[ReadyKit](https://github.com/level09/readykit)** — a complete multi-tenant SaaS template with Stripe billing, OAuth, and team collaboration built on Enferno. [Visit readykit.dev](https://readykit.dev)


![Enferno Demo](docs/enferno-demo.gif)

Key Features
===========
- **Modern Stack**: Python 3.11+, Flask, Vue 3, Vuetify 3
- **Authentication**: Flask-Security with role-based access control
- **OAuth Integration**: Google and GitHub login via Flask-Dance
- **Database**: SQLAlchemy ORM with PostgreSQL/SQLite support
- **Task Queue**: Celery with Redis for background tasks
- **Frontend**: Client-side Vue.js with Vuetify components
- **Security**: CSRF protection, secure session handling
- **Docker Ready**: Production-grade Docker configuration
- **Cursor Rules**: Smart IDE-based code generation and assistance
- **Package Management**: Modern uv workflow with pyproject.toml

Frontend Features
---------------
- Vue.js without build tools - direct browser integration
- Vuetify Material Design components
- Axios for API calls
- Snackbar notifications pattern
- Dialog forms pattern
- Data table server pattern
- Authentication state integration
- Material Design Icons

OAuth Integration
---------------
Supports social login with:
- Google (profile and email scope)
- GitHub (user:email scope)

Configure in `.env`:
```bash
# Google OAuth
GOOGLE_AUTH_ENABLED=true
GOOGLE_OAUTH_CLIENT_ID=your_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret

# GitHub OAuth
GITHUB_AUTH_ENABLED=true
GITHUB_OAUTH_CLIENT_ID=your_client_id
GITHUB_OAUTH_CLIENT_SECRET=your_client_secret
```

Prerequisites
------------
- Python 3.11+
- Redis (for caching and sessions)
- PostgreSQL (optional, SQLite works for development)
- Git
- uv (fast Python package installer and resolver)

Quick Start
----------

### Local Setup

1. Install uv:
```bash
# Install using pip
pip install uv

# Or using the installer script
curl -sSf https://astral.sh/uv/install.sh | bash
```

2. Clone and setup:
```bash
git clone git@github.com:level09/enferno.git
cd enferno
./setup.sh  # Creates environment, installs requirements, generates secure .env
```

3. Initialize and run (modern uv workflow):
```bash
uv run flask create-db  # Setup database
uv run flask install    # Create admin user
uv run flask run        # Start development server
```

For Unix deployments that need uWSGI, install the optional extra:
```bash
uv sync --extra wsgi
```

Or activate environment manually:
```bash
source .venv/bin/activate  # Linux/Mac
# source .venv/Scripts/activate  # Windows
flask create-db && flask install && flask run
```

### Docker Setup

One-command setup with Docker:
```bash
docker compose up --build
```

The Docker setup includes:
- Redis for caching and session management
- PostgreSQL database
- Nginx for serving static files
- Celery for background tasks

Configuration
------------

Key environment variables (.env):

```bash
# Core
FLASK_APP=run.py
FLASK_DEBUG=1  # 0 in production
SECRET_KEY=your_secret_key

# Database (choose one)
SQLALCHEMY_DATABASE_URI=sqlite:///enferno.sqlite3
# Or for PostgreSQL:
# SQLALCHEMY_DATABASE_URI=postgresql://username:password@localhost/dbname

# Redis & Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Email Settings (optional)
MAIL_SERVER=smtp.example.com
MAIL_PORT=465
MAIL_USE_SSL=True
MAIL_USERNAME=your_email
MAIL_PASSWORD=your_password
SECURITY_EMAIL_SENDER=noreply@example.com

# OAuth (optional)
GOOGLE_AUTH_ENABLED=true
GOOGLE_OAUTH_CLIENT_ID=your_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret

GITHUB_AUTH_ENABLED=true
GITHUB_OAUTH_CLIENT_ID=your_client_id
GITHUB_OAUTH_CLIENT_SECRET=your_client_secret

# Security Settings
SECURITY_PASSWORD_SALT=your_secure_salt
SECURITY_TOTP_SECRETS=your_totp_secrets
```

Security Features
---------------
- Two-factor authentication (2FA)
- WebAuthn support
- OAuth integration
- Password policies
- Session protection
- CSRF protection
- Secure cookie settings
- Rate limiting
- XSS protection

For detailed documentation, visit [docs.enferno.io](https://docs.enferno.io)

Contributing
-----------
Contributions welcome! Please read our [Contributing Guide](CONTRIBUTING.md).

License
-------
MIT licensed.

