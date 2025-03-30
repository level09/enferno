Project Enferno
=================

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation Status](https://readthedocs.org/projects/enferno/badge/?version=latest)](https://enferno.readthedocs.io/en/latest/?badge=latest)

A modern Python web framework built on top of Flask, designed for rapid development of secure and scalable web applications. Enferno combines best practices with pre-configured components to help you build production-ready applications quickly.

![Enferno Demo](https://github.com/level09/enferno/blob/master/docs/enferno-hero.gif)

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
- **Package Management**: Fast installation with uv

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
./setup.sh  # Creates Python environment, installs requirements, and generates secure .env
```

3. Initialize application:
```bash
flask create-db  # Setup database
flask install    # Create admin user
```

4. Run development server:
```bash
flask run
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

For detailed documentation, visit [enferno.readthedocs.io](https://enferno.readthedocs.io)

Contributing
-----------
Contributions welcome! Please read our [Contributing Guide](CONTRIBUTING.md).

License
-------
MIT licensed.
