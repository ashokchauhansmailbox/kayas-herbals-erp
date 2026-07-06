"""FastAPI dependency wiring."""

from __future__ import annotations

import uuid
from typing import Annotated, AsyncIterator

from app.core.errors import DomainError
from app.core.security import AuthError, TokenClaims, verify_token
from app.db.session import get_session_factory
from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield a session that auto-commits on success, rolls back on error."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


DbSession = Annotated[AsyncSession, Depends(get_db)]


def _extract_bearer(authorization: str | None) -> str:
    if not authorization:
        raise AuthError("auth.missing_bearer", "Authorization header missing")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthError(
            "auth.malformed_bearer", "Authorization must be 'Bearer <token>'"
        )
    return parts[1]


async def get_token_claims(
    authorization: Annotated[str | None, Header()] = None,
) -> TokenClaims:
    return verify_token(_extract_bearer(authorization))


TokenClaimsDep = Annotated[TokenClaims, Depends(get_token_claims)]


async def get_current_user(
    request: Request,
    claims: TokenClaimsDep,
    db: DbSession,
):
    """Load the local `users` row + effective permissions (cached on request.state)."""
    # Import inside function to avoid circular import at module load.
    from app.services.auth_service import load_current_principal

    cached = getattr(request.state, "principal", None)
    if cached is not None and cached.claims.jti == claims.jti:
        return cached
    principal = await load_current_principal(db, claims)
    request.state.principal = principal
    return principal


class ForbiddenError(DomainError):
    def __init__(self, permission: str):
        super().__init__(
            code="rbac.forbidden",
            message=f"Missing permission: {permission}",
            status=403,
            details={"permission": permission},
        )


def require(permission: str):
    """Return a FastAPI dependency that asserts the current user has `permission`."""

    async def _checker(request: Request, principal=Depends(get_current_user)):
        if permission not in principal.permissions:
            raise ForbiddenError(permission)
        return principal

    _checker.__name__ = f"require_{permission.replace('.', '_')}"
    return _checker


def request_id(request: Request) -> str:
    """Stable per-request correlation id (X-Request-Id) — created if absent."""
    existing = getattr(request.state, "request_id", None)
    if existing:
        return existing
    rid = request.headers.get("X-Request-Id") or uuid.uuid4().hex
    request.state.request_id = rid
    return rid


RequestId = Annotated[str, Depends(request_id)]
