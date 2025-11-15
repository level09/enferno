"""Workspace management service for multi-tenant operations."""

from functools import wraps

from flask import abort, g, session
from flask_security import current_user

from enferno.extensions import db
from enferno.user.models import Membership, Workspace


def get_current_workspace():
    """Get current workspace object from session"""
    workspace_id = session.get("current_workspace_id")
    return db.session.get(Workspace, workspace_id) if workspace_id else None


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

            # Fetch workspace and membership in one query (avoid duplicate lookups)
            workspace = db.session.get(Workspace, workspace_id)
            if not workspace:
                abort(404, "Workspace not found")

            # Verify user has access to this workspace
            membership = db.session.execute(
                db.select(Membership).where(
                    Membership.workspace_id == workspace_id,
                    Membership.user_id == current_user.id,
                )
            ).scalar_one_or_none()

            if not membership:
                abort(403, "Access denied to workspace")

            # Check role requirements
            if required_role == "admin" and membership.role != "admin":
                abort(403, "Admin access required")

            # Set workspace context after all security checks pass
            session["current_workspace_id"] = workspace_id
            g.current_workspace = workspace
            g.user_workspace_role = membership.role

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def workspace_query(model_class):
    """Helper to create workspace-scoped queries"""
    workspace_id = session.get("current_workspace_id")
    if not workspace_id:
        raise ValueError("No workspace context available")
    return db.select(model_class).where(model_class.workspace_id == workspace_id)


class WorkspaceService:
    """Simple workspace business logic"""

    @staticmethod
    def create_workspace(name, owner_user, auto_name=False):
        """Create new workspace with owner as admin

        Args:
            name: Workspace name (ignored if auto_name=True)
            owner_user: User who will own the workspace
            auto_name: If True, generate friendly name from user data
        """
        from sqlalchemy.exc import IntegrityError

        # Auto-generate name for OAuth/self-service signups
        if auto_name:
            if owner_user.name:
                name = f"{owner_user.name.split()[0]}'s Workspace"
            elif owner_user.email:
                name = f"{owner_user.email.split('@')[0]}'s Workspace"
            else:
                name = "My Workspace"

        slug = Workspace.generate_slug(name)
        original_slug = slug
        counter = 1
        max_attempts = 100

        # Try creating workspace with unique slug
        # DB constraint enforces uniqueness, catch and retry with suffix
        for attempt in range(max_attempts):
            try:
                with db.session.begin_nested():
                    workspace = Workspace(name=name, slug=slug, owner_id=owner_user.id)
                    db.session.add(workspace)
                    db.session.flush()  # Get workspace.id and trigger constraint check

                    # Add owner as admin
                    membership = Membership(
                        workspace_id=workspace.id, user_id=owner_user.id, role="admin"
                    )
                    db.session.add(membership)

                db.session.commit()
                return workspace
            except IntegrityError as e:
                db.session.rollback()
                # If slug collision, try with suffix
                if "slug" in str(e).lower() or "unique" in str(e).lower():
                    slug = f"{original_slug}-{counter}"
                    counter += 1
                    if attempt >= max_attempts - 1:
                        raise ValueError(
                            "Failed to create workspace: too many slug conflicts"
                        ) from e
                else:
                    # Other integrity error
                    raise ValueError(f"Failed to create workspace: {str(e)}") from e

    @staticmethod
    def add_member(workspace_id, user, role="member"):
        """Add user to workspace (caller must commit)"""
        # Validate role
        if role not in {"admin", "member"}:
            raise ValueError(f"Invalid role: {role}")

        # Check for existing membership
        existing = db.session.execute(
            db.select(Membership).where(
                Membership.workspace_id == workspace_id, Membership.user_id == user.id
            )
        ).scalar_one_or_none()

        if existing:
            raise ValueError("User is already a member of this workspace")

        membership = Membership(workspace_id=workspace_id, user_id=user.id, role=role)
        db.session.add(membership)
        return membership

    @staticmethod
    def remove_member(workspace_id, user_id):
        """Remove user from workspace"""
        # Check if user is workspace owner
        workspace = db.session.get(Workspace, workspace_id)
        if workspace and workspace.owner_id == user_id:
            raise ValueError("Cannot remove workspace owner")

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
        # Validate role
        if new_role not in {"admin", "member"}:
            raise ValueError(f"Invalid role: {new_role}")

        # Check if user is workspace owner
        workspace = db.session.get(Workspace, workspace_id)
        if workspace and workspace.owner_id == user_id:
            raise ValueError("Cannot change workspace owner's role")

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
        workspace_id = session.get("current_workspace_id")
        if not workspace_id:
            return None

        return db.session.execute(
            db.select(cls).where(cls.id == record_id, cls.workspace_id == workspace_id)
        ).scalar_one_or_none()
