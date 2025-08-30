import dataclasses
import secrets
import string
from datetime import datetime
from uuid import uuid4

from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_security import AsaList
from flask_security.core import RoleMixin, UserMixin
from flask_security.utils import hash_password
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Table,
)
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import declared_attr, relationship

from enferno.extensions import db
from enferno.utils.base import BaseMixin

roles_users: Table = db.Table(
    "roles_users",
    Column("user_id", Integer, ForeignKey("user.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("role.id"), primary_key=True),
)


@dataclasses.dataclass
class Role(db.Model, RoleMixin, BaseMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=True)
    description = db.Column(db.String(255), nullable=True)

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "description": self.description}

    def from_dict(self, json_dict):
        self.name = json_dict.get("name", self.name)
        self.description = json_dict.get("description", self.description)
        return self


@dataclasses.dataclass
class User(UserMixin, db.Model, BaseMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=True)
    fs_uniquifier = db.Column(
        db.String(255), unique=True, nullable=False, default=(lambda _: uuid4().hex)
    )
    name = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    email = db.Column(db.String(255), nullable=True)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=False, nullable=True)
    is_superadmin = db.Column(db.Boolean, default=False, nullable=False)

    roles = relationship("Role", secondary=roles_users, backref="users")

    confirmed_at = db.Column(db.DateTime, nullable=True)
    last_login_at = db.Column(db.DateTime, nullable=True)
    current_login_at = db.Column(db.DateTime, nullable=True)
    last_login_ip = db.Column(db.String(255), nullable=True)
    current_login_ip = db.Column(db.String(255), nullable=True)
    login_count = db.Column(db.Integer, nullable=True)

    # web authn
    fs_webauthn_user_handle = db.Column(db.String(64), unique=True, nullable=True)
    tf_phone_number = db.Column(db.String(64), nullable=True)
    tf_primary_method = db.Column(db.String(140), nullable=True)
    tf_totp_secret = db.Column(db.String(255), nullable=True)
    mf_recovery_codes = db.Column(db.JSON, nullable=True)

    @declared_attr
    def webauthn(cls):
        return relationship("WebAuthn", backref="users", cascade="all, delete")

    def to_dict(self):
        return {
            "id": self.id,
            "active": self.active,
            "name": self.name,
            "username": self.username,
            "email": self.email,
            "is_superadmin": self.is_superadmin,
        }

    def from_dict(self, json_dict):
        self.name = json_dict.get("name", self.name)
        self.username = json_dict.get("username", self.username)
        self.email = json_dict.get("email", self.email)
        if (
            "password" in json_dict
        ):  # Only hash password if provided, to avoid hashing None
            self.password = hash_password(json_dict["password"])
        self.active = json_dict.get("active", self.active)
        return self

    def __str__(self) -> str:
        """
        Return the string representation of the object, typically using its ID.
        """
        return f"{self.id}"

    def __repr__(self) -> str:
        """
        Return an unambiguous string representation of the object.
        """
        return f"{self.username} {self.id} {self.email}"

    meta = {
        "allow_inheritance": True,
        "indexes": ["-created_at", "email", "username"],
        "ordering": ["-created_at"],
    }

    @staticmethod
    def random_password(length=32):
        alphabet = string.ascii_letters + string.digits + string.punctuation
        password = "".join(secrets.choice(alphabet) for i in range(length))
        return hash_password(password)

    def get_workspaces(self):
        """Get all workspaces user has access to"""
        from sqlalchemy import select

        return (
            db.session.execute(
                select(Workspace)
                .join(Membership)
                .where(Membership.user_id == self.id)
                .order_by(Workspace.created_at.desc())
            )
            .scalars()
            .all()
        )

    def get_workspace_role(self, workspace_id):
        """Get user's role in a specific workspace"""
        membership = db.session.execute(
            db.select(Membership).where(
                Membership.user_id == self.id, Membership.workspace_id == workspace_id
            )
        ).scalar_one_or_none()
        return membership.role if membership else None

    def can_access_workspace(self, workspace_id):
        """Check if user can access workspace"""
        return self.get_workspace_role(workspace_id) is not None

    def is_workspace_admin(self, workspace_id):
        """Check if user is admin of workspace"""
        return self.get_workspace_role(workspace_id) == "admin"


class WebAuthn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    credential_id = db.Column(
        db.LargeBinary(1024), index=True, nullable=False, unique=True
    )
    public_key = db.Column(db.LargeBinary(1024), nullable=False)
    sign_count = db.Column(db.Integer, default=0, nullable=False)
    transports = db.Column(MutableList.as_mutable(AsaList()), nullable=True)
    extensions = db.Column(db.String(255), nullable=True)
    lastuse_datetime = db.Column(db.DateTime, nullable=False)
    name = db.Column(db.String(64), nullable=False)
    usage = db.Column(db.String(64), nullable=False)
    backup_state = db.Column(db.Boolean, nullable=False)
    device_type = db.Column(db.String(64), nullable=False)

    @declared_attr
    def user_id(cls):
        return db.Column(
            db.String(64),
            db.ForeignKey("user.fs_webauthn_user_handle", ondelete="CASCADE"),
            nullable=False,
        )

    def get_user_mapping(self):
        """
        Return the mapping from webauthn back to User
        """
        return {"id": self.user_id}


class OAuth(OAuthConsumerMixin, db.Model):
    __tablename__ = "oauth"
    provider_user_id = db.Column(db.String(256), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    user = db.relationship(
        User,
        backref=db.backref(
            "oauth_accounts", cascade="all, delete-orphan", lazy="dynamic"
        ),
    )


class Activity(db.Model, BaseMixin):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(255), nullable=False)
    data = db.Column(db.JSON, nullable=True)

    @classmethod
    def register(cls, user_id, action, data=None):
        """Register an activity for audit purposes"""
        activity = cls(user_id=user_id, action=action, data=data)
        db.session.add(activity)
        try:
            db.session.commit()
            return activity
        except Exception as e:
            print(f"Error registering activity: {e}")
            db.session.rollback()
            return None


@dataclasses.dataclass
class Workspace(db.Model, BaseMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    owner = relationship("User", backref="owned_workspaces")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @staticmethod
    def generate_slug(name):
        """Generate URL-safe slug from name"""
        from sluggi import slugify

        return slugify(name)


@dataclasses.dataclass
class Membership(db.Model, BaseMixin):
    workspace_id = db.Column(
        db.Integer, db.ForeignKey("workspace.id", ondelete="CASCADE"), primary_key=True
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), primary_key=True
    )
    role = db.Column(
        db.String(20), nullable=False, default="member"
    )  # 'admin' or 'member'

    workspace = relationship("Workspace", backref="memberships")
    user = relationship("User", backref="memberships")

    def to_dict(self):
        return {
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "role": self.role,
            "user": self.user.to_dict() if self.user else None,
            "workspace": self.workspace.to_dict() if self.workspace else None,
        }
