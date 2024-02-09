import json, dataclasses
from typing import Dict
from uuid import uuid4
from enferno.utils.base import BaseMixin
from enferno.extensions import db
from flask_security.core import UserMixin, RoleMixin
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Boolean, Column, ForeignKey, Table, ARRAY, LargeBinary, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr

roles_users: Table = db.Table(
    'roles_users',
    Column('user_id', Integer, ForeignKey('user.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('role.id'), primary_key=True)
)


@dataclasses.dataclass
class Role(db.Model, RoleMixin, BaseMixin):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    def to_dict(self) -> Dict:
        return dict(id=self.id, name=self.name, description=self.description)
@dataclasses.dataclass
class User(UserMixin, db.Model, BaseMixin):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
    fs_uniquifier: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, default=uuid4().hex)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)

    roles = relationship('Role', secondary=roles_users, backref="users")

    confirmed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_login_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    current_login_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_login_ip: Mapped[str] = mapped_column(String(255), nullable=True)
    current_login_ip: Mapped[str] = mapped_column(String(255), nullable=True)
    login_count: Mapped[int] = mapped_column(Integer, nullable=True)



    # web authn
    fs_webauthn_user_handle: Mapped[str] = mapped_column(String(64), unique=True, nullable=True)
    tf_phone_number: Mapped[str] = mapped_column(String(64), nullable=True)
    tf_primary_method: Mapped[str] = mapped_column(String(140), nullable=True)
    tf_totp_secret: Mapped[str] = mapped_column(String(255), nullable=True)
    mf_recovery_codes: Mapped[json] = mapped_column(JSON, nullable=True)


    @declared_attr
    def webauthn(cls):
        return relationship("WebAuthn", backref="users", cascade="all, delete")

    def __str__(self) -> str:
        """
        Return the string representation of the object, typically using its ID.
        """
        return f'{self.id}'


    def __repr__(self) -> str:
        """
        Return an unambiguous string representation of the object.
        """
        return f"{self.username} {self.id} {self.email}"


    meta = {
        'allow_inheritance': True,
        'indexes': ['-created_at', 'email', 'username'],
        'ordering': ['-created_at']
    }


class WebAuthn(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    credential_id: Mapped[bytes] = mapped_column(LargeBinary(1024), index=True, nullable=False, unique=True)
    public_key: Mapped[bytes] = mapped_column(LargeBinary(1024), nullable=False)
    sign_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    transports: Mapped[json] = mapped_column(JSON, nullable=True)
    extensions: Mapped[str] = mapped_column(String(255), nullable=True)
    lastuse_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    usage: Mapped[str] = mapped_column(String(64), nullable=False)
    backup_state: Mapped[bool] = mapped_column(Boolean, nullable=False)
    device_type: Mapped[str] = mapped_column(String(64), nullable=False)

    @declared_attr
    def user_id(cls):
        return db.Column(
            db.Integer,
            db.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        )

    def get_user_mapping(self):
        """
        Return the mapping from webauthn back to User
        """
        return dict(id=self.user_id)
