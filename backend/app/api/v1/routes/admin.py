"""Role + Permission catalogue routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select

from app.deps import DbSession, RequestId, require
from app.models.identity import Permission, Role, RolePermission
from app.schemas.admin import PermissionOut, RoleCreateIn, RoleOut, RoleUpdateIn
from app.services.audit_service import AuditContext
from app.services.auth_service import Principal

roles_router = APIRouter()
permissions_router = APIRouter()


async def _serialize_role(db, role: Role) -> RoleOut:
    codes = (
        (
            await db.execute(
                select(Permission.code)
                .join(RolePermission, RolePermission.permission_id == Permission.id)
                .where(RolePermission.role_id == role.id)
            )
        )
        .scalars()
        .all()
    )
    return RoleOut(
        id=role.id,
        code=role.code,
        name=role.name,
        description=role.description,
        is_system=role.is_system,
        permissions=sorted(codes),
    )


async def _batch_perms_for_roles(
    db, role_ids: list
) -> dict:
    if not role_ids:
        return {}
    rows = (
        await db.execute(
            select(RolePermission.role_id, Permission.code)
            .join(Permission, Permission.id == RolePermission.permission_id)
            .where(RolePermission.role_id.in_(role_ids))
        )
    ).all()
    out: dict = {rid: [] for rid in role_ids}
    for rid, code in rows:
        out[rid].append(code)
    return out


async def _assign_role_permissions(
    db, role: Role, codes: list[str], *, replace: bool
) -> None:
    """Assign `codes` to `role`, batch-fetching permissions in a single query.

    - `replace=True`  : wipe existing role→permission rows first (update path).
    - `replace=False` : only insert (create path, no pre-existing rows).

    Raises HTTPException(400) with the first unknown permission code.
    """
    if replace:
        await db.execute(
            delete(RolePermission).where(RolePermission.role_id == role.id)
        )
    if not codes:
        return
    perms = {
        p.code: p
        for p in (
            await db.execute(select(Permission).where(Permission.code.in_(codes)))
        ).scalars()
    }
    missing = [c for c in codes if c not in perms]
    if missing:
        raise HTTPException(400, f"Unknown permission: {missing[0]}")
    for pcode in codes:
        db.add(RolePermission(role_id=role.id, permission_id=perms[pcode].id))


@roles_router.get(
    "", response_model=list[RoleOut], dependencies=[Depends(require("roles.read"))]
)
async def list_roles(db: DbSession) -> list[RoleOut]:
    roles = (await db.execute(select(Role).order_by(Role.code))).scalars().all()
    perms_by_role = await _batch_perms_for_roles(db, [r.id for r in roles])
    return [
        RoleOut(
            id=r.id,
            code=r.code,
            name=r.name,
            description=r.description,
            is_system=r.is_system,
            permissions=sorted(perms_by_role.get(r.id, [])),
        )
        for r in roles
    ]


@roles_router.get(
    "/{code}", response_model=RoleOut, dependencies=[Depends(require("roles.read"))]
)
async def get_role(code: str, db: DbSession) -> RoleOut:
    role = (
        await db.execute(select(Role).where(Role.code == code))
    ).scalar_one_or_none()
    if role is None:
        raise HTTPException(404, "Role not found")
    return await _serialize_role(db, role)


@roles_router.post("", response_model=RoleOut, status_code=201)
async def create_role(
    payload: RoleCreateIn,
    db: DbSession,
    request_id: RequestId,
    principal: Principal = Depends(require("roles.manage")),
) -> RoleOut:
    if (
        await db.execute(select(Role).where(Role.code == payload.code))
    ).scalar_one_or_none():
        raise HTTPException(409, f"Role code exists: {payload.code}")
    role = Role(
        code=payload.code,
        name=payload.name,
        description=payload.description,
        is_system=False,
    )
    db.add(role)
    await db.flush()
    await _assign_role_permissions(db, role, payload.permissions, replace=False)
    async with AuditContext(
        db,
        actor_id=principal.id,
        entity="role",
        entity_id=role.id,
        action="create",
        request_id=request_id,
    ) as ctx:
        ctx.before = None
        ctx.after = {"code": role.code, "permissions": list(payload.permissions)}
    return await _serialize_role(db, role)


@roles_router.patch("/{code}", response_model=RoleOut)
async def update_role(
    code: str,
    payload: RoleUpdateIn,
    db: DbSession,
    request_id: RequestId,
    principal: Principal = Depends(require("roles.manage")),
) -> RoleOut:
    role = (
        await db.execute(select(Role).where(Role.code == code))
    ).scalar_one_or_none()
    if role is None:
        raise HTTPException(404, "Role not found")
    if role.is_system:
        raise HTTPException(400, "Cannot edit system role")
    before = {"name": role.name, "description": role.description}
    async with AuditContext(
        db,
        actor_id=principal.id,
        entity="role",
        entity_id=role.id,
        action="update",
        request_id=request_id,
    ) as ctx:
        ctx.before = before
        if payload.name is not None:
            role.name = payload.name
        if payload.description is not None:
            role.description = payload.description
        if payload.permissions is not None:
            await _assign_role_permissions(
                db, role, payload.permissions, replace=True
            )
        ctx.after = {"name": role.name, "description": role.description}
    return await _serialize_role(db, role)


@roles_router.delete("/{code}", status_code=204, response_model=None)
async def delete_role(
    code: str,
    db: DbSession,
    request_id: RequestId,
    principal: Principal = Depends(require("roles.manage")),
) -> None:
    role = (
        await db.execute(select(Role).where(Role.code == code))
    ).scalar_one_or_none()
    if role is None:
        raise HTTPException(404, "Role not found")
    if role.is_system:
        raise HTTPException(400, "Cannot delete system role")
    async with AuditContext(
        db,
        actor_id=principal.id,
        entity="role",
        entity_id=role.id,
        action="delete",
        request_id=request_id,
    ) as ctx:
        ctx.before = {"code": role.code}
        ctx.after = None
        await db.delete(role)


@permissions_router.get(
    "",
    response_model=list[PermissionOut],
    dependencies=[Depends(require("permissions.read"))],
)
async def list_permissions(
    db: DbSession, module: str | None = None
) -> list[PermissionOut]:
    stmt = select(Permission)
    if module:
        stmt = stmt.where(Permission.module == module)
    stmt = stmt.order_by(Permission.module, Permission.code)
    rows = (await db.execute(stmt)).scalars().all()
    return [PermissionOut.model_validate(r) for r in rows]
