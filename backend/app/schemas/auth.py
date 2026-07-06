"""Auth-related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import EmailStr, Field

from app.schemas.common import ORMModel


class MeOut(ORMModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    status: str
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    last_login_at: Optional[datetime] = None


class SessionOut(ORMModel):
    id: UUID
    jti: str
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    expires_at: datetime
    revoked_at: Optional[datetime] = None


class RevokeSessionIn(ORMModel):
    jti: str
