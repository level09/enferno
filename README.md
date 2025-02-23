Project Enferno
=================

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation Status](https://readthedocs.org/projects/enferno/badge/?version=latest)](https://enferno.readthedocs.io/en/latest/?badge=latest)

A modern Python web framework built on top of Flask, designed for rapid development of secure and scalable web applications. Enferno combines best practices with pre-configured components to help you build production-ready applications quickly.

![alt Enferno Demo](https://github.com/level09/enferno/blob/master/docs/enferno-hero.gif)

![alt Users Management](https://github.com/level09/enferno/blob/master/docs/users-management.jpg)

![alt Roles Management](https://github.com/level09/enferno/blob/master/docs/roles-management.jpg)

http://enferno.io

What's New
==============
- **Social Authentication**: OAuth integration with Google and GitHub
- **OpenAI Integration**: AI-powered code generation tools
- **Modern UI**: Updated Vue 3 and Vuetify components

Features
==================

Core Features:
- **Modern Stack**: Built on Flask with Python 3.12 support
- **User Management**: Authentication, registration, and role-based access control
- **Social Login**: OAuth integration with Google and GitHub
- **Frontend**: Vue 3 and Vuetify 3
- **Database**: SQLAlchemy ORM with PostgreSQL support
- **Task Queue**: Celery integration
- **Email**: Flask-Mail integration
- **Security**: Flask-Security integration
- **Docker**: Docker configuration included
- **AI Integration**: OpenAI integration
- **Internationalization**: Flask-Babel integration
- **CLI Tools**: Flask CLI commands

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
```

3. Configure and initialize:
```bash
# Update settings in .env file
flask create-db  # Initialize the database
flask install    # Create the first admin user
```

4. Run the development server:
```bash
flask run
```

### Docker Setup

1. Clone and configure:
```bash
git clone git@github.com:level09/enferno.git
cd enferno
./generate-env.sh  # Creates .env file with secure random keys
# Update settings in .env file
```

2. Build and run with Docker Compose:
```bash
docker compose up --build
```

Running Background Tasks
----------------------

Start Celery worker:
```bash
celery -A enferno.tasks worker -l info
```

Environment Variables
-------------------

Available configuration options in `.env`:

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

# OAuth Settings
GOOGLE_AUTH_ENABLED=true  # Enable/disable Google OAuth
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret

GITHUB_AUTH_ENABLED=true  # Enable/disable GitHub OAuth
GITHUB_OAUTH_CLIENT_ID=your_github_client_id
GITHUB_OAUTH_CLIENT_SECRET=your_github_client_secret

# Security
SECURITY_PASSWORD_SALT=your_secure_salt
SECURITY_TOTP_SECRETS=your_totp_secrets
```

OAuth Configuration
-----------------

### Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google+ API
4. Configure OAuth consent screen
5. Create OAuth 2.0 credentials
6. Add authorized redirect URI: `http://your-domain/login/google/authorized`
7. Set environment variables:
```bash
GOOGLE_AUTH_ENABLED=true
GOOGLE_OAUTH_CLIENT_ID=your_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret
```

### GitHub OAuth

1. Go to GitHub Settings > Developer Settings > OAuth Apps
2. Create New OAuth App
3. Set Homepage URL to your domain
4. Set Authorization callback URL: `http://your-domain/login/github/authorized`
5. Set environment variables:
```bash
GITHUB_AUTH_ENABLED=true
GITHUB_OAUTH_CLIENT_ID=your_client_id
GITHUB_OAUTH_CLIENT_SECRET=your_client_secret
```

### Adding New Providers

The OAuth system supports additional providers through Flask-Dance. To add a new provider:

1. Add provider configuration to `settings.py`
2. Create and register the provider blueprint in `app.py`
3. Add provider-specific data fetching in `get_oauth_user_data()`
4. Update the login template to add the new provider button

Contributing
-----------
Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

License
-------
MIT licensed.
