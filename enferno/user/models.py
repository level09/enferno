import dataclasses
import secrets
import string
from datetime import datetime
from uuid import uuid4

from quart import g
from quart_security import RoleMixin, UserMixin, hash_password
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Table,
    UniqueConstraint,
    select,
)
from sqlalchemy.orm import declared_attr, relationship

from enferno.extensions import Base

roles_users = Table(
    "roles_users",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("user.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("role.id"), primary_key=True),
)


@dataclasses.dataclass
class Role(Base, RoleMixin):
    __tablename__ = "role"

    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True, nullable=True)
    description = Column(String(255), nullable=True)

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "description": self.description}

    def from_dict(self, json_dict):
        self.name = json_dict.get("name", self.name)
        self.description = json_dict.get("description", self.description)
        return self


@dataclasses.dataclass
class User(Base, UserMixin):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=True)
    fs_uniquifier = Column(
        String(255), unique=True, nullable=False, default=lambda: uuid4().hex
    )
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    password_set = Column(Boolean, default=True, nullable=False)
    active = Column(Boolean, default=False, nullable=True)

    roles = relationship(
        "Role", secondary=roles_users, backref="users", lazy="selectin"
    )

    confirmed_at = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    current_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String(255), nullable=True)
    current_login_ip = Column(String(255), nullable=True)
    login_count = Column(Integer, nullable=True)

    # web authn
    fs_webauthn_user_handle = Column(String(64), unique=True, nullable=True)
    tf_phone_number = Column(String(64), nullable=True)
    tf_primary_method = Column(String(140), nullable=True)
    tf_totp_secret = Column(String(255), nullable=True)
    mf_recovery_codes = Column(JSON, nullable=True)

    @declared_attr
    def webauthn(cls):
        return relationship(
            "WebAuthn", backref="users", cascade="all, delete", lazy="selectin"
        )

    @property
    def display_name(self):
        return self.name or self.email

    @property
    def has_usable_password(self):
        return self.password_set

    def to_dict(self):
        return {
            "id": self.id,
            "active": self.active,
            "name": self.name,
            "email": self.email,
            "roles": [role.to_dict() for role in self.roles],
        }

    async def from_dict(self, json_dict):
        self.name = json_dict.get("name", self.name)
        self.username = json_dict.get("username", self.username)
        self.email = json_dict.get("email", self.email)
        if "password" in json_dict:
            self.password = hash_password(json_dict["password"])
        if "roles" in json_dict:
            role_ids = [r.get("id") for r in json_dict["roles"]]
            if role_ids:
                result = await g.db_session.execute(
                    select(Role).filter(Role.id.in_(role_ids))
                )
                self.roles = list(result.scalars().all())
        self.active = json_dict.get("active", self.active)
        return self

    def __str__(self) -> str:
        return f"{self.id}"

    def __repr__(self) -> str:
        return f"<User {self.id}: {self.email}>"

    @staticmethod
    def random_password(length=32):
        alphabet = string.ascii_letters + string.digits + string.punctuation
        password = "".join(secrets.choice(alphabet) for i in range(length))
        return hash_password(password)

    async def logout_other_sessions(self, current_session_token=None):
        await Session.deactivate_user_sessions(
            self.id, exclude_token=current_session_token
        )

    def get_active_sessions(self):
        return [s for s in self.sessions if s.is_active]

    @property
    def two_factor_devices(self):
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


class WebAuthn(Base):
    __tablename__ = "web_authn"

    id = Column(Integer, primary_key=True)
    credential_id = Column(LargeBinary(1024), index=True, nullable=False, unique=True)
    public_key = Column(LargeBinary(1024), nullable=False)
    sign_count = Column(Integer, default=0, nullable=False)
    transports = Column(JSON, nullable=True)
    extensions = Column(String(255), nullable=True)
    lastuse_datetime = Column(DateTime, nullable=False)
    name = Column(String(64), nullable=False)
    usage = Column(String(64), nullable=False)
    backup_state = Column(Boolean, nullable=False)
    device_type = Column(String(64), nullable=False)

    @declared_attr
    def user_id(cls):
        return Column(
            String(64),
            ForeignKey("user.fs_webauthn_user_handle", ondelete="CASCADE"),
            nullable=False,
        )

    def get_user_mapping(self):
        return {"fs_webauthn_user_handle": self.user_id}


class OAuth(Base):
    __tablename__ = "oauth"

    id = Column(Integer, primary_key=True)
    provider = Column(String(50), nullable=False)
    provider_user_id = Column(String(256), nullable=False)
    token = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    user = relationship(
        "User",
        backref="oauth_accounts",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_user"),
    )


class Activity(Base):
    __tablename__ = "activity"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    action = Column(String(255), nullable=False)
    data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    @classmethod
    async def register(cls, user_id, action, data=None):
        activity = cls(user_id=user_id, action=action, data=data)
        g.db_session.add(activity)
        try:
            from enferno.websocket import broadcast

            await broadcast({"type": "activity", "action": action, "user_id": user_id})
        except Exception:
            pass  # don't fail DB ops if WS broadcast fails
        return activity


class Session(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    user = relationship("User", backref="sessions", lazy="selectin")

    session_token = Column(String(255), unique=True, nullable=False)
    last_active = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime, nullable=True)
    ip_address = Column(String(255), nullable=True)

    meta = Column(JSON, nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

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
    async def create_session(cls, user_id, session_token, ip_address=None, meta=None):
        result = await g.db_session.execute(
            select(cls).filter_by(session_token=session_token)
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.user_id = user_id
            existing.ip_address = ip_address
            existing.meta = meta
            existing.is_active = True
            existing.last_active = datetime.now()
            g.db_session.add(existing)
            return existing

        session_record = cls(
            user_id=user_id,
            session_token=session_token,
            ip_address=ip_address,
            meta=meta,
            is_active=True,
        )
        g.db_session.add(session_record)
        return session_record

    @classmethod
    async def deactivate_user_sessions(cls, user_id, exclude_token=None):
        stmt = (
            cls.__table__.update()
            .where(cls.user_id == user_id)
            .where(cls.is_active == True)  # noqa: E712
        )
        if exclude_token:
            stmt = stmt.where(cls.session_token != exclude_token)
        stmt = stmt.values(is_active=False)
        await g.db_session.execute(stmt)
