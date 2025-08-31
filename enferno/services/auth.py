"""
Authentication and authorization utilities following Enferno patterns
"""

from functools import wraps

from flask import abort, jsonify
from flask_security import current_user

from enferno.extensions import db


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

    @staticmethod
    def create_user_workspace(user, provider_data):
        """Create workspace for new OAuth user and make them admin."""
        from enferno.user.models import Membership, Workspace

        # Generate workspace name from user data with fallbacks
        name = provider_data.get("name", "").strip()
        email = provider_data.get("email", "").strip()

        if name:
            # Use first name if available
            workspace_name = name.split()[0] + "'s Workspace"
        elif email:
            # Fall back to email prefix
            workspace_name = email.split("@")[0] + "'s Workspace"
        else:
            # Ultimate fallback
            workspace_name = "My Workspace"

        # Create workspace with unique slug handling
        base_slug = Workspace.generate_slug(workspace_name)
        final_slug = base_slug
        counter = 1

        # Ensure unique slug
        while db.session.execute(
            db.select(Workspace).where(Workspace.slug == final_slug)
        ).scalar_one_or_none():
            final_slug = f"{base_slug}-{counter}"
            counter += 1

        workspace = Workspace(name=workspace_name, slug=final_slug, owner_id=user.id)
        db.session.add(workspace)
        db.session.flush()  # Get workspace ID

        # Make user admin of their workspace
        membership = Membership(
            user_id=user.id, workspace_id=workspace.id, role="admin"
        )
        db.session.add(membership)

        return workspace
