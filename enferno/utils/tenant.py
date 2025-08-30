"""Simple tenant utilities for workspace context."""

from functools import wraps

from flask import abort, g, session
from flask_security import current_user

from enferno.extensions import db
from enferno.user.models import Membership, Workspace


def get_current_workspace_id():
    """Get current workspace ID from session"""
    return session.get("current_workspace_id")


def set_current_workspace(workspace_id):
    """Set current workspace in session"""
    session["current_workspace_id"] = workspace_id


def get_current_workspace():
    """Get current workspace object"""
    workspace_id = get_current_workspace_id()
    if not workspace_id:
        return None
    return db.session.get(Workspace, workspace_id)


def require_workspace_access(required_role="member"):
    """Decorator to require workspace access with specific role"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)

            # Get workspace_id from URL parameter
            workspace_id = kwargs.get("workspace_id")
            if not workspace_id:
                abort(400, "No workspace specified")

            # Verify user has access to this workspace
            user_role = current_user.get_workspace_role(workspace_id)
            if not user_role:
                abort(403, "Access denied to workspace")

            # Check role requirements
            if required_role == "admin" and user_role != "admin":
                abort(403, "Admin access required")

            # Only set session after all security checks pass
            set_current_workspace(workspace_id)

            # Store workspace in g for easy access in views
            g.current_workspace = get_current_workspace()
            g.user_workspace_role = user_role

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def workspace_query(model_class):
    """Helper to create workspace-scoped queries"""
    workspace_id = get_current_workspace_id()
    if not workspace_id:
        raise ValueError("No workspace context available")
    return db.select(model_class).where(model_class.workspace_id == workspace_id)


class WorkspaceService:
    """Simple workspace business logic"""

    @staticmethod
    def create_workspace(name, owner_user):
        """Create new workspace with owner as admin"""
        slug = Workspace.generate_slug(name)

        # Ensure unique slug
        counter = 1
        original_slug = slug
        while db.session.execute(
            db.select(Workspace).where(Workspace.slug == slug)
        ).scalar_one_or_none():
            slug = f"{original_slug}-{counter}"
            counter += 1

        workspace = Workspace(name=name, slug=slug, owner_id=owner_user.id)
        db.session.add(workspace)
        db.session.commit()

        # Add owner as admin
        membership = Membership(
            workspace_id=workspace.id, user_id=owner_user.id, role="admin"
        )
        db.session.add(membership)
        db.session.commit()

        return workspace

    @staticmethod
    def add_member(workspace_id, user, role="member"):
        """Add user to workspace"""
        membership = Membership(workspace_id=workspace_id, user_id=user.id, role=role)
        db.session.add(membership)
        db.session.commit()
        return membership

    @staticmethod
    def remove_member(workspace_id, user_id):
        """Remove user from workspace"""
        membership = db.session.execute(
            db.select(Membership).where(
                Membership.workspace_id == workspace_id, Membership.user_id == user_id
            )
        ).scalar_one_or_none()

        if membership:
            db.session.delete(membership)
            db.session.commit()
            return True
        return False

    @staticmethod
    def update_member_role(workspace_id, user_id, new_role):
        """Update user's role in workspace"""
        membership = db.session.execute(
            db.select(Membership).where(
                Membership.workspace_id == workspace_id, Membership.user_id == user_id
            )
        ).scalar_one_or_none()

        if membership:
            membership.role = new_role
            db.session.commit()
            return membership
        return False


class WorkspaceScoped:
    """Mixin for models that belong to workspaces"""

    @classmethod
    def for_current_workspace(cls):
        """Get all records for current workspace"""
        return db.session.execute(workspace_query(cls)).scalars().all()

    @classmethod
    def get_by_id(cls, record_id):
        """Get record by ID within current workspace"""
        workspace_id = get_current_workspace_id()
        if not workspace_id:
            return None

        return db.session.execute(
            db.select(cls).where(cls.id == record_id, cls.workspace_id == workspace_id)
        ).scalar_one_or_none()
