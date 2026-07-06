"""Auth routes.

- GET /auth/me         → current principal + effective roles/permissions
- GET /auth/sessions   → active + revoked sessions for the current user
- POST /auth/logout    → revoke the current JWT's jti
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.deps import DbSession, get_current_user
from app.models.identity import Session as SessionRow
from app.models.identity import User
from app.schemas.auth import MeOut, SessionOut
from app.services.audit_service import log_activity
from app.services.auth_service import Principal, revoke_session
from fastapi import APIRouter, Depends
from sqlalchemy import select

router = APIRouter()


@router.get("/me", response_model=MeOut)
async def me(
    db: DbSession,
    principal: Principal = Depends(get_current_user),
) -> MeOut:
    u: User = principal.user
    # Track last_login_at on every /me hit — safe under session token lifetime.
    u.last_login_at = datetime.now(timezone.utc)
    await log_activity(
        db, actor_id=u.id, event="auth.me", entity="user", entity_id=u.id
    )
    return MeOut(
        id=u.id,
        email=u.email,
        full_name=u.full_name,
        status=u.status,
        roles=list(principal.roles),
        permissions=sorted(principal.permissions),
        last_login_at=u.last_login_at,
    )


@router.get("/sessions", response_model=list[SessionOut])
async def list_sessions(
    db: DbSession,
    principal: Principal = Depends(get_current_user),
) -> list[SessionOut]:
    rows = (
        (
            await db.execute(
                select(SessionRow)
                .where(SessionRow.user_id == principal.id)
                .order_by(SessionRow.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return [SessionOut.model_validate(r) for r in rows]


@router.post("/logout", status_code=204, response_model=None)
async def logout(
    db: DbSession,
    principal: Principal = Depends(get_current_user),
) -> None:
    if principal.claims.jti:
        await revoke_session(db, jti=principal.claims.jti)
    await log_activity(
        db,
        actor_id=principal.id,
        event="auth.logout",
        entity="session",
        payload={"jti": principal.claims.jti},
    )
