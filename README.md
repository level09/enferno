Project Enferno
=================

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation Status](https://readthedocs.org/projects/enferno/badge/?version=latest)](https://enferno.readthedocs.io/en/latest/?badge=latest)

A modern Python web framework built on top of Flask, designed for rapid development of secure and scalable web applications. Enferno combines best practices with pre-configured components to help you build production-ready applications quickly.

![alt Enferno Demo](https://github.com/level09/enferno/blob/master/docs/enferno-hero.gif)

![alt Users Management](https://github.com/level09/enferno/blob/master/docs/users-management.jpg)

![alt Roles Management](https://github.com/level09/enferno/blob/master/docs/roles-management.jpg)

http://enferno.io

Enferno Framework Update: OpenAI Integration 
==============
Enferno now includes powerful OpenAI integration! This feature allows for rapid generation of Flask Views, Templates, and Models using natural language. Streamline your development process by creating base code samples that can be customized to fit your needs.

New Commands:
- `flask generate-model`: Instantly generate models with natural language
- `flask generate-dashboard`: Create dashboards by describing your requirements
- `flask generate-api`: Speed up API development with verbal descriptions
- `flask generate-env`: Generate secure environment files with random keys

This update boosts your productivity by reducing development time and making the coding process more intuitive.

Features
==================

Core Features:
- **Modern Stack**: Built on Flask with Python 3.12 support
- **User Management**: Built-in authentication, registration, and role-based access control
- **Frontend**: Integrated Vue 3 and Vuetify 3 for modern, responsive UIs
- **Database**: SQLAlchemy ORM with PostgreSQL support
- **Task Queue**: Background job processing with Celery
- **Email**: Easy email integration with Flask-Mail
- **Security**: Best practices out of the box
- **Docker**: Production-ready Docker configuration with non-root security
- **AI Integration**: OpenAI-powered code generation tools
- **Internationalization**: Multi-language support via Flask-Babel
- **CLI Tools**: Powerful command-line utilities for common tasks

AI-Powered Features
-----------------

Enferno comes with built-in AI commands that help you generate code using natural language:

1. Generate a Model:
```bash
flask generate-model --class_name User --fields "name as string, email as string unique, age as integer, created_at as datetime"
```

2. Generate an API:
```bash
flask generate-api --class_name Product --fields "name, description as text, price as decimal, stock as integer"
```

3. Generate a Dashboard:
```bash
flask generate-dashboard --class_name Order --fields "order_number, customer_name, total_amount as decimal, status as string"
```

The AI commands use OpenAI's GPT models to generate boilerplate code while following best practices and project conventions. Make sure to set your OpenAI API key in the environment variables.

Prerequisites
-------------

* Python 3.12+
* Redis
* PostgreSQL
* Node.js (for frontend development)

Quick Start
----------

### Local Development

1. Clone the repository:
```bash
git clone git@github.com:level09/enferno.git
cd enferno
```

2. Set up environment and install dependencies:
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
pip install -r requirements.txt
./generate-env.sh  # Creates .env file with secure random keys
# Edit additional settings in .env
```

3. Initialize the database:
```bash
flask create-db
flask install
```

4. Run the development server:
```bash
flask run
```

### Using Docker (Recommended for Production)

1. Clone and configure:
```bash
git clone git@github.com:level09/enferno.git
cd enferno
./generate-env.sh  # Creates .env file with secure random keys
# Edit additional settings in .env
```

2. Build and run with Docker Compose:
```bash
docker compose up --build
```

The application will be available at:
- Web: http://localhost

Running Background Tasks
----------------------

### Local Development
```bash
celery -A enferno.tasks worker -l info
# Add -b flag to enable Celery heartbeat (periodic tasks)
```

### Docker Environment
Background tasks are automatically handled by the Celery container.

Environment Variables
-------------------

Key configuration options in `.env`:

```bash
# Core Settings
SECRET_KEY=your_secret_key
FLASK_APP=run.py
FLASK_DEBUG=1  # Set to 0 in production

# Database
SQLALCHEMY_DATABASE_URI=postgresql://username:password@localhost/dbname

# Redis
REDIS_PASSWORD=your_redis_password
SESSION_REDIS=redis://:password@localhost:6379/1
CELERY_BROKER_URL=redis://:password@localhost:6379/2
CELERY_RESULT_BACKEND=redis://:password@localhost:6379/3

# OpenAI Integration
OPENAI_API_KEY=your_openai_key

# Security
SECURITY_PASSWORD_SALT=your_secure_salt
SECURITY_TOTP_SECRETS=your_totp_secrets
```

Security Notes
-------------
- All Docker services run as non-root users
- Configuration files are mounted read-only
- Sensitive data is managed through environment variables
- Static files are served through Nginx
- Redis is password-protected
- Secure key generation via `flask generate-env`

Contributing
-----------
Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

License
-------
MIT licensed.
