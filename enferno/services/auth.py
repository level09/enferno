"""
Authentication and authorization decorators following Enferno patterns
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
