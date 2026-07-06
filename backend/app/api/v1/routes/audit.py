"""Audit + activity log read routes."""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from app.deps import DbSession, require
from app.models.identity import ActivityLog, AuditLog
from app.schemas.admin import ActivityLogOut, AuditLogOut
from app.schemas.common import Page

router = APIRouter()


@router.get("/logs", response_model=Page[AuditLogOut], dependencies=[Depends(require("audit.read"))])
async def list_audit(
    db: DbSession,
    page: int = 1,
    page_size: int = 50,
    entity: str | None = None,
    entity_id: uuid.UUID | None = None,
    actor_id: uuid.UUID | None = None,
    action: str | None = None,
    since: datetime | None = None,
) -> Page[AuditLogOut]:
    stmt = select(AuditLog)
    if entity:
        stmt = stmt.where(AuditLog.entity == entity)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if actor_id:
        stmt = stmt.where(AuditLog.actor_id == actor_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if since:
        stmt = stmt.where(AuditLog.at >= since)
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    rows = (
        await db.execute(
            stmt.order_by(AuditLog.at.desc()).offset((page - 1) * page_size).limit(page_size)
        )
    ).scalars().all()
    return Page[AuditLogOut](
        items=[AuditLogOut.model_validate(r) for r in rows],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/activity", response_model=Page[ActivityLogOut], dependencies=[Depends(require("audit.read"))])
async def list_activity(
    db: DbSession,
    page: int = 1,
    page_size: int = 50,
    event: str | None = None,
    actor_id: uuid.UUID | None = None,
) -> Page[ActivityLogOut]:
    stmt = select(ActivityLog)
    if event:
        stmt = stmt.where(ActivityLog.event == event)
    if actor_id:
        stmt = stmt.where(ActivityLog.actor_id == actor_id)
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    rows = (
        await db.execute(
            stmt.order_by(ActivityLog.at.desc()).offset((page - 1) * page_size).limit(page_size)
        )
    ).scalars().all()
    return Page[ActivityLogOut](
        items=[ActivityLogOut.model_validate(r) for r in rows],
        page=page,
        page_size=page_size,
        total=total,
    )
