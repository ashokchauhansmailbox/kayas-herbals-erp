"""User, Role, Permission, Invitation, Audit schemas — all in one compact module."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import EmailStr, Field

from app.schemas.common import ORMModel


# -------------------- Users --------------------
class UserOut(ORMModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None
    status: str
    two_factor_enabled: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    roles: list[str] = Field(default_factory=list)


class UserUpdateIn(ORMModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None  # invited | active | suspended | deleted


class UserRoleAssignIn(ORMModel):
    role_code: str


# -------------------- Roles / Permissions --------------------
class PermissionOut(ORMModel):
    id: UUID
    code: str
    module: str
    description: Optional[str] = None


class RoleOut(ORMModel):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    is_system: bool
    permissions: list[str] = Field(default_factory=list)


class RoleCreateIn(ORMModel):
    code: str
    name: str
    description: Optional[str] = None
    permissions: list[str] = Field(default_factory=list)


class RoleUpdateIn(ORMModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[list[str]] = None


# -------------------- Invitations --------------------
class InvitationCreateIn(ORMModel):
    email: EmailStr
    role_code: str


class InvitationOut(ORMModel):
    id: UUID
    email: EmailStr
    role_id: UUID
    token: str
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    created_at: datetime


# -------------------- Audit --------------------
class AuditLogOut(ORMModel):
    id: UUID
    actor_id: Optional[UUID] = None
    actor_role: Optional[str] = None
    entity: str
    entity_id: Optional[UUID] = None
    action: str
    before: Optional[dict[str, Any]] = None
    after: Optional[dict[str, Any]] = None
    diff: Optional[dict[str, Any]] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    at: datetime


class ActivityLogOut(ORMModel):
    id: UUID
    actor_id: Optional[UUID] = None
    event: str
    entity: Optional[str] = None
    entity_id: Optional[UUID] = None
    payload: Optional[dict[str, Any]] = None
    ip: Optional[str] = None
    at: datetime
