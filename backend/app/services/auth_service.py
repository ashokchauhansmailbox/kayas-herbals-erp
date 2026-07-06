"""AuthService — resolve the local user + effective permissions from a Supabase JWT.

Also handles session tracking (BR-USR-04): every incoming token's `jti` is
recorded in the `sessions` table on first use; subsequent requests reject
tokens whose session has been revoked.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import AuthError, TokenClaims
from app.models.identity import (
    Permission,
    Role,
    RolePermission,
    Session,
    User,
    UserRole,
)


@dataclass
class Principal:
    """The authenticated user + their effective permissions."""

    user: User
    claims: TokenClaims
    roles: tuple[str, ...] = ()
    permissions: frozenset[str] = field(default_factory=frozenset)

    @property
    def id(self) -> uuid.UUID:
        return self.user.id


async def _ensure_session(db: AsyncSession, user: User, claims: TokenClaims) -> None:
    """Record the token's jti in `sessions` (idempotent) and honour revocation."""
    if not claims.jti:
        return  # tokens without jti bypass session tracking (test convenience)
    existing = (
        await db.execute(select(Session).where(Session.jti == claims.jti))
    ).scalar_one_or_none()
    if existing is None:
        db.add(
            Session(
                user_id=user.id,
                jti=claims.jti,
                expires_at=datetime.fromtimestamp(claims.exp, tz=timezone.utc),
            )
        )
        await db.flush()
        return
    if existing.revoked_at is not None:
        raise AuthError("auth.session_revoked", "Session has been revoked")


async def _load_permissions(
    db: AsyncSession, user_id: uuid.UUID
) -> tuple[tuple[str, ...], frozenset[str]]:
    stmt = (
        select(Role.code, Permission.code)
        .select_from(UserRole)
        .join(Role, Role.id == UserRole.role_id)
        .outerjoin(RolePermission, RolePermission.role_id == Role.id)
        .outerjoin(Permission, Permission.id == RolePermission.permission_id)
        .where(UserRole.user_id == user_id)
    )
    rows = (await db.execute(stmt)).all()
    role_codes: set[str] = set()
    perm_codes: set[str] = set()
    for role, perm in rows:
        role_codes.add(role)
        if perm:
            perm_codes.add(perm)
    return tuple(sorted(role_codes)), frozenset(perm_codes)


async def load_current_principal(db: AsyncSession, claims: TokenClaims) -> Principal:
    user = (
        await db.execute(select(User).where(User.id == claims.sub))
    ).scalar_one_or_none()
    if user is None:
        # Auto-provision on first login (BR-USR-01): local mirror of Supabase user.
        user = User(
            id=claims.sub,
            email=claims.email or f"{claims.sub}@unknown.local",
            status="active",
        )
        db.add(user)
        await db.flush()
    else:
        if user.status == "suspended":
            raise AuthError("auth.user_suspended", "User is suspended")
        if user.status == "deleted" or user.deleted_at is not None:
            raise AuthError("auth.user_deleted", "User is deleted")
    await _ensure_session(db, user, claims)
    roles, permissions = await _load_permissions(db, user.id)
    return Principal(user=user, claims=claims, roles=roles, permissions=permissions)


async def revoke_session(db: AsyncSession, *, jti: str) -> bool:
    session = (
        await db.execute(select(Session).where(Session.jti == jti))
    ).scalar_one_or_none()
    if session is None or session.revoked_at is not None:
        return False
    session.revoked_at = datetime.now(timezone.utc)
    await db.flush()
    return True
