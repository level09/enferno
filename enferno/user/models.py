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
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    password_set = db.Column(db.Boolean, default=True, nullable=False)
    active = db.Column(db.Boolean, default=False, nullable=True)

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

    @property
    def display_name(self):
        """Return best available display name for UI."""
        return self.name or self.email

    @property
    def has_usable_password(self):
        """Check if user has a password they actually know.

        OAuth users are created with password_set=False. Once they set
        a password via the change password form, password_set becomes True.
        """
        return self.password_set

    def to_dict(self):
        return {
            "id": self.id,
            "active": self.active,
            "name": self.name,
            "email": self.email,
            "roles": [role.to_dict() for role in self.roles],
        }

    def from_dict(self, json_dict):
        self.name = json_dict.get("name", self.name)
        self.username = json_dict.get("username", self.username)
        self.email = json_dict.get("email", self.email)
        if (
            "password" in json_dict
        ):  # Only hash password if provided, to avoid hashing None
            self.password = hash_password(json_dict["password"])
        # Update roles if specified, otherwise leave unchanged
        if "roles" in json_dict:
            role_ids = [r.get("id") for r in json_dict["roles"]]
            self.roles = (
                Role.query.filter(Role.id.in_(role_ids)).all()
                if role_ids
                else self.roles
            )
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
        return f"<User {self.id}: {self.email}>"

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

    def logout_other_sessions(self, current_session_token=None):
        """Logout all other sessions for this user."""
        from enferno.user.models import Session

        Session.deactivate_user_sessions(self.id, exclude_token=current_session_token)

    def get_active_sessions(self):
        """Get all active sessions for this user."""
        return [s for s in self.sessions if s.is_active]

    @property
    def two_factor_devices(self):
        """Get a unified list of all 2FA methods/devices."""
        devices = []
        if self.tf_primary_method:
            devices.append(
                {"type": self.tf_primary_method, "name": "Authenticator App"}
            )
        if self.webauthn:
            for wan in self.webauthn:
                devices.append(
                    {"type": "webauthn", "name": wan.name, "usage": wan.usage}
                )
        return devices


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
        Return the mapping from webauthn back to User.
        Since user_id is fs_webauthn_user_handle, we need to map it correctly.
        """
        return {"fs_webauthn_user_handle": self.user_id}


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
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    @classmethod
    def register(cls, user_id, action, data=None):
        """Register an activity for audit purposes.

        Note: Does not commit - caller is responsible for transaction management.
        This prevents activity logging from rolling back other pending changes.
        """
        activity = cls(user_id=user_id, action=action, data=data)
        db.session.add(activity)
        return activity


class Session(db.Model, BaseMixin):
    """Track active user sessions for session management."""

    __tablename__ = "user_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref=db.backref("sessions", lazy=True))

    session_token = db.Column(db.String(255), unique=True, nullable=False)
    last_active = db.Column(db.DateTime, default=datetime.now)
    expires_at = db.Column(db.DateTime, nullable=True)
    ip_address = db.Column(db.String(255), nullable=True)

    # Browser, OS, device metadata
    meta = db.Column(db.JSON, nullable=True)

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "ip_address": self.ip_address,
            "meta": self.meta,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def create_session(cls, user_id, session_token, ip_address=None, meta=None):
        """Create or update a session for a user.

        Uses get-or-create pattern to avoid unique constraint violations
        that would rollback other pending changes (like password updates).
        """
        # Try to find existing session first
        existing = cls.query.filter_by(session_token=session_token).first()
        if existing:
            # Update existing session
            existing.user_id = user_id
            existing.ip_address = ip_address
            existing.meta = meta
            existing.is_active = True
            existing.last_active = datetime.now()
            db.session.add(existing)
            return existing

        # Create new session
        session_record = cls(
            user_id=user_id,
            session_token=session_token,
            ip_address=ip_address,
            meta=meta,
            is_active=True,
        )
        db.session.add(session_record)
        return session_record

    @classmethod
    def deactivate_user_sessions(cls, user_id, exclude_token=None):
        """Deactivate all sessions for a user, optionally excluding current."""
        query = cls.query.filter_by(user_id=user_id, is_active=True)
        if exclude_token:
            query = query.filter(cls.session_token != exclude_token)
        query.update({"is_active": False})
        db.session.commit()
