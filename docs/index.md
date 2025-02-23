# Enferno Framework Documentation

## Overview

Enferno is a modern Python web framework built on top of Flask, designed for rapid development of secure and scalable web applications. It combines best practices with pre-configured components to help you build production-ready applications quickly.

## Key Features

- **Modern Stack**: Python 3.11+, Flask, Vue 3, Vuetify 3
- **Authentication**: Flask-Security with role-based access control
- **OAuth Integration**: Google and GitHub login via Flask-Dance
- **Database**: SQLAlchemy ORM with PostgreSQL/SQLite support
- **Task Queue**: Celery with Redis for background tasks
- **AI Features**: OpenAI-powered code generation tools
- **Frontend**: Client-side Vue.js with Vuetify components
- **Docker Ready**: Production-grade Docker configuration

## Documentation Sections

- [Getting Started](getting-started.md) - Installation and setup guide
- [Authentication](authentication.md) - User management and OAuth setup
- [Development](development.md) - Development guidelines and best practices
- [Deployment](deployment.md) - Production deployment guide

## AI Code Generation

Generate boilerplate code using natural language:

```bash
# Generate a model
flask generate-model --class_name User --fields "name:string, email:string:unique"

# Generate an API
flask generate-api --class_name Product --fields "name, price:decimal"

# Generate a dashboard
flask generate-dashboard --class_name Order --fields "order_number, total:decimal"
```

## OAuth Integration

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

## Source Code

The source code is available on [GitHub](https://github.com/level09/enferno).

## Contributing

We welcome contributions! Please read our [Contributing Guide](https://github.com/level09/enferno/blob/master/CONTRIBUTING.md) for details.
