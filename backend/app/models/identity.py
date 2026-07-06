"""Identity & Access models.

Tables:
    users
    roles
    permissions
    role_permissions
    user_roles
    sessions
    user_invitations
    audit_logs
    activity_logs

Design principles (see docs/architecture/02-database-schema.md):
    * `users.id` is shared with Supabase Auth user id (no password column here).
    * Roles + permissions are the RBAC substrate (docs/architecture/05-rbac.md).
    * Audit vs activity distinction lives in docs/architecture/06-audit-activity.md.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin, VersionMixin
from app.db.types import PGUUID, jsonb_column, uuid_pk


# ---------------------------------------------------------------------------
# users
# ---------------------------------------------------------------------------
class User(Base, TimestampMixin, SoftDeleteMixin, VersionMixin):
    __tablename__ = "users"

    # id matches Supabase auth.users.id — DO NOT auto-generate on insert.
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(
            "invited",
            "active",
            "suspended",
            "deleted",
            name="user_status",
            create_type=False,
        ),
        nullable=False,
        server_default=text("'invited'"),
    )
    two_factor_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_users_email", "email"),
        Index("ix_users_status", "status"),
    )


# ---------------------------------------------------------------------------
# roles / permissions / mapping
# ---------------------------------------------------------------------------
class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    id = uuid_pk()
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )

    __table_args__ = (Index("ix_roles_code", "code"),)


class Permission(Base, TimestampMixin):
    __tablename__ = "permissions"

    id = uuid_pk()
    code: Mapped[str] = mapped_column(String(96), nullable=False, unique=True)
    module: Mapped[str] = mapped_column(String(48), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_permissions_code", "code"),
        Index("ix_permissions_module", "module"),
    )


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    permission_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    # PK (role_id, permission_id) already enforces uniqueness — no extra UQ needed.


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    assigned_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    # PK (user_id, role_id) already enforces uniqueness — no extra UQ needed.


# ---------------------------------------------------------------------------
# sessions (refresh session tracking for Supabase JWT)
# ---------------------------------------------------------------------------
class Session(Base, TimestampMixin):
    __tablename__ = "sessions"

    id = uuid_pk()
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    jti: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    ip: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_sessions_user_id", "user_id"),
        Index("ix_sessions_jti", "jti"),
    )


# ---------------------------------------------------------------------------
# user_invitations
# ---------------------------------------------------------------------------
class UserInvitation(Base, TimestampMixin):
    __tablename__ = "user_invitations"

    id = uuid_pk()
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    token: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    invited_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_user_invitations_email", "email"),
        Index("ix_user_invitations_token", "token"),
    )


# ---------------------------------------------------------------------------
# audit_logs — append-only, protected by immutability trigger (migration 012)
# ---------------------------------------------------------------------------
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = uuid_pk()
    actor_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    actor_role: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    entity: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    before = jsonb_column(nullable=True)
    after = jsonb_column(nullable=True)
    diff = jsonb_column(nullable=True)
    ip: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    __table_args__ = (
        Index("ix_audit_logs_entity", "entity", "entity_id", "at"),
        Index("ix_audit_logs_actor_id", "actor_id", "at"),
        Index("ix_audit_logs_at", "at"),
    )


# ---------------------------------------------------------------------------
# activity_logs — high-volume, purgeable
# ---------------------------------------------------------------------------
class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = uuid_pk()
    actor_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    event: Mapped[str] = mapped_column(String(96), nullable=False)
    entity: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    entity_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    payload = jsonb_column(nullable=True)
    ip: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    __table_args__ = (
        Index("ix_activity_logs_actor_id", "actor_id", "at"),
        Index("ix_activity_logs_event", "event", "at"),
    )


__all__ = [
    "User",
    "Role",
    "Permission",
    "RolePermission",
    "UserRole",
    "Session",
    "UserInvitation",
    "AuditLog",
    "ActivityLog",
]
