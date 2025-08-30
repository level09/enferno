"""
Authentication and authorization utilities following Enferno patterns
"""

from functools import wraps

from flask import abort, jsonify
from flask_security import current_user


def require_superadmin():
    """Decorator to require super admin privileges"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if not current_user.is_superadmin:
                abort(403)
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def require_superadmin_api():
    """Decorator for API endpoints that require super admin"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"error": "Authentication required"}), 401
            if not current_user.is_superadmin:
                return jsonify({"error": "Super admin privileges required"}), 403
            return f(*args, **kwargs)

        return decorated_function

    return decorator


class AuthService:
    """Authentication service following Enferno service patterns"""

    @staticmethod
    def is_superadmin(user=None):
        """Check if user is super admin"""
        if user is None:
            user = current_user
        return user.is_authenticated and user.is_superadmin

    @staticmethod
    def can_create_workspaces(user=None):
        """Check if user can create workspaces"""
        return AuthService.is_superadmin(user)

    @staticmethod
    def can_manage_platform(user=None):
        """Check if user can manage platform-wide settings"""
        return AuthService.is_superadmin(user)
