"""Vendor master CRUD (Sprint 1.4).

Purchase-order / GRN / vendor-invoice transactional endpoints ship in Sprint 1.5
alongside Orders + Billing.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select

from app.deps import DbSession, RequestId, require
from app.models.purchase import Vendor
from app.schemas.common import Page
from app.schemas.purchase import VendorIn, VendorOut, VendorPatch
from app.services.audit_service import AuditContext
from app.services.auth_service import Principal

router = APIRouter()


def _serialize(v: Vendor) -> VendorOut:
    return VendorOut.model_validate(v)


@router.get(
    "",
    response_model=Page[VendorOut],
    dependencies=[Depends(require("purchase.read"))],
)
async def list_vendors(
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    q: str | None = Query(default=None, max_length=64),
    is_active: bool | None = Query(default=None),
) -> Page[VendorOut]:
    stmt = select(Vendor).where(Vendor.deleted_at.is_(None))
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            (Vendor.name.ilike(pattern))
            | (Vendor.code.ilike(pattern))
            | (Vendor.gstin.ilike(pattern))
        )
    if is_active is not None:
        stmt = stmt.where(Vendor.is_active.is_(is_active))
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    rows = (
        await db.execute(
            stmt.order_by(Vendor.code).offset((page - 1) * page_size).limit(page_size)
        )
    ).scalars().all()
    return Page[VendorOut](
        items=[_serialize(r) for r in rows],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/{vendor_id}",
    response_model=VendorOut,
    dependencies=[Depends(require("purchase.read"))],
)
async def get_vendor(vendor_id: UUID, db: DbSession) -> VendorOut:
    row = (
        await db.execute(
            select(Vendor).where(Vendor.id == vendor_id, Vendor.deleted_at.is_(None))
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Vendor not found")
    return _serialize(row)


@router.post("", response_model=VendorOut, status_code=201)
async def create_vendor(
    payload: VendorIn,
    db: DbSession,
    request_id: RequestId,
    principal: Principal = Depends(require("vendors.manage")),
) -> VendorOut:
    if (
        await db.execute(select(Vendor).where(Vendor.code == payload.code))
    ).scalar_one_or_none():
        raise HTTPException(409, f"Vendor code exists: {payload.code}")
    vendor = Vendor(**payload.model_dump(), created_by=principal.id, updated_by=principal.id)
    db.add(vendor)
    await db.flush()
    async with AuditContext(
        db,
        actor_id=principal.id,
        entity="vendor",
        entity_id=vendor.id,
        action="create",
        request_id=request_id,
    ) as ctx:
        ctx.before = None
        ctx.after = payload.model_dump(mode="json")
    return _serialize(vendor)


@router.patch("/{vendor_id}", response_model=VendorOut)
async def update_vendor(
    vendor_id: UUID,
    payload: VendorPatch,
    db: DbSession,
    request_id: RequestId,
    principal: Principal = Depends(require("vendors.manage")),
) -> VendorOut:
    vendor = (
        await db.execute(
            select(Vendor).where(Vendor.id == vendor_id, Vendor.deleted_at.is_(None))
        )
    ).scalar_one_or_none()
    if vendor is None:
        raise HTTPException(404, "Vendor not found")
    before = {
        c.name: getattr(vendor, c.name) for c in Vendor.__table__.columns if c.name != "id"
    }
    changes = payload.model_dump(exclude_unset=True)
    for k, v in changes.items():
        setattr(vendor, k, v)
    vendor.updated_by = principal.id
    async with AuditContext(
        db,
        actor_id=principal.id,
        entity="vendor",
        entity_id=vendor.id,
        action="update",
        request_id=request_id,
    ) as ctx:
        ctx.before = {k: before.get(k) for k in changes}
        ctx.after = changes
    return _serialize(vendor)


@router.delete("/{vendor_id}", status_code=204)
async def delete_vendor(
    vendor_id: UUID,
    db: DbSession,
    request_id: RequestId,
    principal: Principal = Depends(require("vendors.manage")),
) -> None:
    from datetime import datetime, timezone

    vendor = (
        await db.execute(
            select(Vendor).where(Vendor.id == vendor_id, Vendor.deleted_at.is_(None))
        )
    ).scalar_one_or_none()
    if vendor is None:
        raise HTTPException(404, "Vendor not found")
    vendor.deleted_at = datetime.now(timezone.utc)
    vendor.deleted_by = principal.id
    vendor.is_active = False
    async with AuditContext(
        db,
        actor_id=principal.id,
        entity="vendor",
        entity_id=vendor.id,
        action="delete",
        request_id=request_id,
    ) as ctx:
        ctx.before = {"is_active": True}
        ctx.after = {"is_active": False, "deleted_at": vendor.deleted_at.isoformat()}
