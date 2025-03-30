# Getting Started

This guide will help you set up Enferno for local development or production deployment.

## Prerequisites

- Python 3.7 or higher (3.11+ recommended)
- Redis
- PostgreSQL (optional, SQLite works for development)
- Git
- uv (fast Python package installer and resolver)

### Installing Dependencies

**Redis:**

- Mac (using homebrew): `brew install redis`
- Linux: `sudo apt-get install redis-server`

**PostgreSQL (optional):**

- Mac (using homebrew): `brew install postgresql`
- Linux: `sudo apt-get install postgresql`

**uv:**

- Using pip: `pip install uv`
- Using the installer script: `curl -sSf https://astral.sh/uv/install.sh | bash`

## Local Development Setup

### 1. Clone the Repository

```bash
git clone git@github.com:level09/enferno.git
cd enferno
```

### 2. Run Setup Script

```bash
./setup.sh
```

This script will:
- Find the latest Python 3.x version on your system
- Check for uv installation
- Create a virtual environment in `.venv` directory
- Install requirements using uv
- Generate a secure `.env` file with random keys

### 3. Configure Environment

Review and edit `.env` file with your settings. Key configurations:

```bash
# Core Settings
FLASK_APP=run.py
FLASK_DEBUG=1  # Set to 0 in production
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

**Note: Never commit your `.env` file to version control.**

### 4. Initialize Application

If using PostgreSQL:
```bash
createdb enferno  # Create PostgreSQL database
flask create-db   # Setup database tables
flask install     # Create first admin user
```

If using SQLite:
```bash
flask create-db   # This will create enferno.sqlite3
flask install     # Create first admin user
```

### 5. Run Development Server

```bash
flask run
```

The application will be available at `http://localhost:5000`

## Docker Setup

For a quick start with Docker:

```bash
# Clone and configure
git clone git@github.com:level09/enferno.git
cd enferno
./setup.sh  # Creates environment and secure .env

# Build and run
docker compose up --build
```

The Docker setup includes:
- Redis for caching and session management
- PostgreSQL database
- Nginx for serving static files
- Celery for background tasks

## Running Background Tasks

Start Celery worker for background tasks:

```bash
celery -A enferno.tasks worker -l info
```

## Security Features

- Two-factor authentication support
- WebAuthn support
- Password policies
- Session protection
- CSRF protection
- Secure cookie settings

## Next Steps

- Set up [OAuth Authentication](authentication.md)
- Read [Development Guidelines](development.md)
- Learn about [Deployment](deployment.md)
