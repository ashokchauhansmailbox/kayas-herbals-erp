"""User management routes (admin scope)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import DbSession, RequestId, get_current_user, require
from app.models.identity import Role, User, UserRole
from app.schemas.admin import UserOut, UserRoleAssignIn, UserUpdateIn
from app.schemas.common import Page
from app.services.audit_service import AuditContext
from app.services.auth_service import Principal

router = APIRouter()


async def _to_out(db: AsyncSession, user: User) -> UserOut:
    role_codes = (
        await db.execute(
            select(Role.code).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user.id)
        )
    ).scalars().all()
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        status=user.status,
        two_factor_enabled=user.two_factor_enabled,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        roles=list(role_codes),
    )


@router.get("", response_model=Page[UserOut], dependencies=[Depends(require("users.read"))])
async def list_users(
    db: DbSession,
    page: int = 1,
    page_size: int = 25,
    q: str | None = None,
    status: str | None = None,
) -> Page[UserOut]:
    stmt = select(User).where(User.deleted_at.is_(None))
    if q:
        stmt = stmt.where(User.email.ilike(f"%{q}%"))
    if status:
        stmt = stmt.where(User.status == status)
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    users = (
        await db.execute(
            stmt.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        )
    ).scalars().all()
    items = [await _to_out(db, u) for u in users]
    return Page[UserOut](items=items, page=page, page_size=page_size, total=total)


@router.get("/{user_id}", response_model=UserOut, dependencies=[Depends(require("users.read"))])
async def get_user(user_id: uuid.UUID, db: DbSession) -> UserOut:
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        raise HTTPException(404, "User not found")
    return await _to_out(db, user)


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdateIn,
    db: DbSession,
    request_id: RequestId,
    principal: Principal = Depends(require("users.update")),
) -> UserOut:
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        raise HTTPException(404, "User not found")
    before = {"full_name": user.full_name, "phone": user.phone, "status": user.status}
    async with AuditContext(
        db,
        actor_id=principal.id,
        entity="user",
        entity_id=user.id,
        action="update",
        request_id=request_id,
    ) as ctx:
        ctx.before = before
        if payload.full_name is not None:
            user.full_name = payload.full_name
        if payload.phone is not None:
            user.phone = payload.phone
        if payload.status is not None:
            user.status = payload.status
        ctx.after = {"full_name": user.full_name, "phone": user.phone, "status": user.status}
    return await _to_out(db, user)


@router.post("/{user_id}/roles", response_model=UserOut)
async def assign_role(
    user_id: uuid.UUID,
    payload: UserRoleAssignIn,
    db: DbSession,
    request_id: RequestId,
    principal: Principal = Depends(require("roles.assign")),
) -> UserOut:
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        raise HTTPException(404, "User not found")
    role = (await db.execute(select(Role).where(Role.code == payload.role_code))).scalar_one_or_none()
    if role is None:
        raise HTTPException(404, f"Role not found: {payload.role_code}")
    exists = (
        await db.execute(
            select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role.id)
        )
    ).scalar_one_or_none()
    if exists is None:
        async with AuditContext(
            db,
            actor_id=principal.id,
            entity="user_role",
            entity_id=user.id,
            action="create",
            request_id=request_id,
        ) as ctx:
            ctx.before = None
            ctx.after = {"user_id": str(user.id), "role_code": role.code}
            db.add(UserRole(user_id=user.id, role_id=role.id, assigned_by=principal.id))
    return await _to_out(db, user)


@router.delete("/{user_id}/roles/{role_code}", response_model=UserOut)
async def revoke_role(
    user_id: uuid.UUID,
    role_code: str,
    db: DbSession,
    request_id: RequestId,
    principal: Principal = Depends(require("roles.assign")),
) -> UserOut:
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        raise HTTPException(404, "User not found")
    role = (await db.execute(select(Role).where(Role.code == role_code))).scalar_one_or_none()
    if role is None:
        raise HTTPException(404, f"Role not found: {role_code}")
    ur = (
        await db.execute(
            select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role.id)
        )
    ).scalar_one_or_none()
    if ur is not None:
        async with AuditContext(
            db,
            actor_id=principal.id,
            entity="user_role",
            entity_id=user.id,
            action="delete",
            request_id=request_id,
        ) as ctx:
            ctx.before = {"user_id": str(user.id), "role_code": role.code}
            ctx.after = None
            await db.delete(ur)
    return await _to_out(db, user)
