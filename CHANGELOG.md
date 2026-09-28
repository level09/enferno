# Changelog

## Unreleased

### Added
- Offline configuration checks with `uv run python checks.py --config`.
- Setup and configuration regression tests, plus PostgreSQL smoke checks on Python 3.11, 3.12, and 3.13 and a production container build in CI.

### Security
- Stop publishing PostgreSQL and Redis container ports and require explicit database and Redis passwords.
- Update vendored Vue, Vuetify, and Axios assets to the versions tested in ReadyKit 1.5.1.

Thanks to Ali Tanveer ([@alivirgo](https://github.com/alivirgo)) for privately reporting the shared Docker Compose port and default password issues in ReadyKit.

### Fixed
- Require Python 3.11 or newer in setup and install dependencies with the selected interpreter.
- Install and configure optional Redis sessions and Celery with `./setup.sh --full` or Docker setup.
- Generate Docker Redis settings using `REDIS_URL`, preserve the SQLite default for local setup, and enable secure cookies for Docker.
- Check each Celery container through Redis instead of inheriting the image's HTTP health check.
- Install Celery and Redis in the production Docker image. The image synced only the `wsgi` extra while `docker-compose.yml` runs a Celery worker, so `enferno.tasks` always fell back to `CELERY_AVAILABLE = False`.

### Changed
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
- Updated setup.sh script to use uv instead of venv
- Modified Dockerfile to use uv for package installation
- Updated documentation to reference uv

## v11.0 (2023-03-27)

### Added
- New activity model to track user actions like creating and editing users/roles
- Cursor Rules for improved code generation and assistance
- Comprehensive documentation for Cursor Rules approach

### Changed
- Improved user and roles tables design in both frontend and backend
- Transitioned from OpenAI integration to Cursor Rules for code generation
- Enhanced admin user creation with better console output

### Removed
- Removed flask-openai dependency and related code generation commands
- Removed OpenAI API key requirements

### Fixed
- Various UI and UX improvements
- Code cleanup and bug fixes 