# Changelog

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