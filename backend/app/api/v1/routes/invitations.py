"""User invitation routes."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.deps import DbSession, RequestId, require
from app.models.identity import Role, UserInvitation
from app.schemas.admin import InvitationCreateIn, InvitationOut
from app.services.audit_service import AuditContext
from app.services.auth_service import Principal

router = APIRouter()

INVITE_TTL = timedelta(days=7)


@router.get(
    "",
    response_model=list[InvitationOut],
    dependencies=[Depends(require("users.invite"))],
)
async def list_invitations(db: DbSession) -> list[InvitationOut]:
    rows = (
        (
            await db.execute(
                select(UserInvitation).order_by(UserInvitation.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return [InvitationOut.model_validate(r) for r in rows]


@router.post("", response_model=InvitationOut, status_code=201)
async def create_invitation(
    payload: InvitationCreateIn,
    db: DbSession,
    request_id: RequestId,
    principal: Principal = Depends(require("users.invite")),
) -> InvitationOut:
    role = (
        await db.execute(select(Role).where(Role.code == payload.role_code))
    ).scalar_one_or_none()
    if role is None:
        raise HTTPException(404, f"Role not found: {payload.role_code}")
    inv = UserInvitation(
        email=str(payload.email).lower(),
        role_id=role.id,
        token=secrets.token_urlsafe(32),
        expires_at=datetime.now(timezone.utc) + INVITE_TTL,
        invited_by=principal.id,
    )
    db.add(inv)
    await db.flush()
    async with AuditContext(
        db,
        actor_id=principal.id,
        entity="user_invitation",
        entity_id=inv.id,
        action="create",
        request_id=request_id,
    ) as ctx:
        ctx.before = None
        ctx.after = {
            "email": inv.email,
            "role": role.code,
            "expires_at": inv.expires_at.isoformat(),
        }
    return InvitationOut.model_validate(inv)


@router.delete("/{invitation_id}", status_code=204, response_model=None)
async def revoke_invitation(
    invitation_id: uuid.UUID,
    db: DbSession,
    request_id: RequestId,
    principal: Principal = Depends(require("users.invite")),
) -> None:
    inv = (
        await db.execute(
            select(UserInvitation).where(UserInvitation.id == invitation_id)
        )
    ).scalar_one_or_none()
    if inv is None:
        raise HTTPException(404, "Invitation not found")
    if inv.accepted_at is not None:
        raise HTTPException(400, "Invitation already accepted")
    async with AuditContext(
        db,
        actor_id=principal.id,
        entity="user_invitation",
        entity_id=inv.id,
        action="delete",
        request_id=request_id,
    ) as ctx:
        ctx.before = {"email": inv.email, "expires_at": inv.expires_at.isoformat()}
        ctx.after = None
        await db.delete(inv)
