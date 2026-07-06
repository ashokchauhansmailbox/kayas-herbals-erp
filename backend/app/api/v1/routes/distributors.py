"""Distributor + Distributor-Tier CRUD + KYC verification (Sprint 1.4)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select

from app.deps import DbSession, RequestId, require
from app.models.distributor import Distributor, DistributorTier
from app.schemas.common import Page
from app.schemas.distributor import (
    DistributorIn,
    DistributorOut,
    DistributorPatch,
    DistributorTierIn,
    DistributorTierOut,
    DistributorTierPatch,
    KycVerifyIn,
)
from app.services.audit_service import AuditContext
from app.services.auth_service import Principal

tiers_router = APIRouter()
distributors_router = APIRouter()


# ---------------------------------------------------------------------------
# Tiers
# ---------------------------------------------------------------------------
@tiers_router.get(
    "",
    response_model=list[DistributorTierOut],
    dependencies=[Depends(require("distributors.read"))],
)
async def list_tiers(db: DbSession) -> list[DistributorTierOut]:
    rows = (
        await db.execute(
            select(DistributorTier)
            .where(DistributorTier.deleted_at.is_(None))
            .order_by(DistributorTier.sort_order, DistributorTier.code)
        )
    ).scalars().all()
    return [DistributorTierOut.model_validate(r) for r in rows]


@tiers_router.get(
    "/{code}",
    response_model=DistributorTierOut,
    dependencies=[Depends(require("distributors.read"))],
)
async def get_tier(code: str, db: DbSession) -> DistributorTierOut:
    tier = (
        await db.execute(
            select(DistributorTier).where(
                DistributorTier.code == code, DistributorTier.deleted_at.is_(None)
            )
        )
    ).scalar_one_or_none()
    if tier is None:
        raise HTTPException(404, "Tier not found")
    return DistributorTierOut.model_validate(tier)


@tiers_router.post("", response_model=DistributorTierOut, status_code=201)
async def create_tier(
    payload: DistributorTierIn,
    db: DbSession,
    request_id: RequestId,
    principal: Principal = Depends(require("distributors.pricing_manage")),
) -> DistributorTierOut:
    if (
        await db.execute(
            select(DistributorTier).where(DistributorTier.code == payload.code)
        )
    ).scalar_one_or_none():
        raise HTTPException(409, f"Tier code exists: {payload.code}")
    tier = DistributorTier(
        **payload.model_dump(),
        created_by=principal.id,
        updated_by=principal.id,
    )
    db.add(tier)
    await db.flush()
    async with AuditContext(
        db,
        actor_id=principal.id,
        entity="distributor_tier",
        entity_id=tier.id,
        action="create",
        request_id=request_id,
    ) as ctx:
        ctx.before = None
        ctx.after = payload.model_dump(mode="json")
    return DistributorTierOut.model_validate(tier)


@tiers_router.patch("/{code}", response_model=DistributorTierOut)
async def update_tier(
    code: str,
    payload: DistributorTierPatch,
    db: DbSession,
    request_id: RequestId,
    principal: Principal = Depends(require("distributors.pricing_manage")),
) -> DistributorTierOut:
    tier = (
        await db.execute(
            select(DistributorTier).where(
                DistributorTier.code == code, DistributorTier.deleted_at.is_(None)
            )
        )
    ).scalar_one_or_none()
    if tier is None:
        raise HTTPException(404, "Tier not found")
    changes = payload.model_dump(exclude_unset=True)
    for k, v in changes.items():
        setattr(tier, k, v)
    tier.updated_by = principal.id
    async with AuditContext(
        db,
        actor_id=principal.id,
        entity="distributor_tier",
        entity_id=tier.id,
        action="update",
        request_id=request_id,
    ) as ctx:
        ctx.before = {k: getattr(tier, k) for k in changes}
        ctx.after = changes
    return DistributorTierOut.model_validate(tier)


@tiers_router.delete("/{code}", status_code=204)
async def delete_tier(
    code: str,
    db: DbSession,
    request_id: RequestId,
    principal: Principal = Depends(require("distributors.pricing_manage")),
) -> None:
    tier = (
        await db.execute(
            select(DistributorTier).where(
                DistributorTier.code == code, DistributorTier.deleted_at.is_(None)
            )
        )
    ).scalar_one_or_none()
    if tier is None:
        raise HTTPException(404, "Tier not found")
    tier.deleted_at = datetime.now(timezone.utc)
    tier.deleted_by = principal.id
    tier.is_active = False
    async with AuditContext(
        db,
        actor_id=principal.id,
        entity="distributor_tier",
        entity_id=tier.id,
        action="delete",
        request_id=request_id,
    ) as ctx:
        ctx.before = {"is_active": True}
        ctx.after = {"is_active": False}


# ---------------------------------------------------------------------------
# Distributors
# ---------------------------------------------------------------------------
@distributors_router.get(
    "",
    response_model=Page[DistributorOut],
    dependencies=[Depends(require("distributors.read"))],
)
async def list_distributors(
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    q: str | None = Query(default=None, max_length=64),
    kyc_status: str | None = Query(default=None, pattern="^(pending|submitted|verified|rejected)$"),
) -> Page[DistributorOut]:
    stmt = select(Distributor).where(Distributor.deleted_at.is_(None))
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            (Distributor.business_name.ilike(pattern))
            | (Distributor.code.ilike(pattern))
            | (Distributor.gstin.ilike(pattern))
        )
    if kyc_status:
        stmt = stmt.where(Distributor.kyc_status == kyc_status)
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    rows = (
        await db.execute(
            stmt.order_by(Distributor.code).offset((page - 1) * page_size).limit(page_size)
        )
    ).scalars().all()
    return Page[DistributorOut](
        items=[DistributorOut.model_validate(r) for r in rows],
        page=page,
        page_size=page_size,
        total=total,
    )


@distributors_router.get(
    "/{distributor_id}",
    response_model=DistributorOut,
    dependencies=[Depends(require("distributors.read"))],
)
async def get_distributor(distributor_id: UUID, db: DbSession) -> DistributorOut:
    row = (
        await db.execute(
            select(Distributor).where(
                Distributor.id == distributor_id, Distributor.deleted_at.is_(None)
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Distributor not found")
    return DistributorOut.model_validate(row)


@distributors_router.post("", response_model=DistributorOut, status_code=201)
async def create_distributor(
    payload: DistributorIn,
    db: DbSession,
    request_id: RequestId,
    principal: Principal = Depends(require("distributors.manage")),
) -> DistributorOut:
    if (
        await db.execute(select(Distributor).where(Distributor.code == payload.code))
    ).scalar_one_or_none():
        raise HTTPException(409, f"Distributor code exists: {payload.code}")
    dist = Distributor(
        **payload.model_dump(),
        created_by=principal.id,
        updated_by=principal.id,
    )
    db.add(dist)
    await db.flush()
    async with AuditContext(
        db,
        actor_id=principal.id,
        entity="distributor",
        entity_id=dist.id,
        action="create",
        request_id=request_id,
    ) as ctx:
        ctx.before = None
        ctx.after = payload.model_dump(mode="json")
    return DistributorOut.model_validate(dist)


@distributors_router.patch("/{distributor_id}", response_model=DistributorOut)
async def update_distributor(
    distributor_id: UUID,
    payload: DistributorPatch,
    db: DbSession,
    request_id: RequestId,
    principal: Principal = Depends(require("distributors.manage")),
) -> DistributorOut:
    dist = (
        await db.execute(
            select(Distributor).where(
                Distributor.id == distributor_id, Distributor.deleted_at.is_(None)
            )
        )
    ).scalar_one_or_none()
    if dist is None:
        raise HTTPException(404, "Distributor not found")
    changes = payload.model_dump(exclude_unset=True)
    for k, v in changes.items():
        setattr(dist, k, v)
    dist.updated_by = principal.id
    async with AuditContext(
        db,
        actor_id=principal.id,
        entity="distributor",
        entity_id=dist.id,
        action="update",
        request_id=request_id,
    ) as ctx:
        ctx.before = {k: getattr(dist, k) for k in changes}
        ctx.after = changes
    return DistributorOut.model_validate(dist)


@distributors_router.delete("/{distributor_id}", status_code=204)
async def delete_distributor(
    distributor_id: UUID,
    db: DbSession,
    request_id: RequestId,
    principal: Principal = Depends(require("distributors.manage")),
) -> None:
    dist = (
        await db.execute(
            select(Distributor).where(
                Distributor.id == distributor_id, Distributor.deleted_at.is_(None)
            )
        )
    ).scalar_one_or_none()
    if dist is None:
        raise HTTPException(404, "Distributor not found")
    dist.deleted_at = datetime.now(timezone.utc)
    dist.deleted_by = principal.id
    dist.is_active = False
    async with AuditContext(
        db,
        actor_id=principal.id,
        entity="distributor",
        entity_id=dist.id,
        action="delete",
        request_id=request_id,
    ) as ctx:
        ctx.before = {"is_active": True}
        ctx.after = {"is_active": False}


@distributors_router.post("/{distributor_id}/kyc", response_model=DistributorOut)
async def verify_kyc(
    distributor_id: UUID,
    payload: KycVerifyIn,
    db: DbSession,
    request_id: RequestId,
    principal: Principal = Depends(require("distributors.kyc_verify")),
) -> DistributorOut:
    dist = (
        await db.execute(
            select(Distributor).where(
                Distributor.id == distributor_id, Distributor.deleted_at.is_(None)
            )
        )
    ).scalar_one_or_none()
    if dist is None:
        raise HTTPException(404, "Distributor not found")
    if payload.status == "rejected" and not payload.rejection_reason:
        raise HTTPException(400, "rejection_reason is required for status=rejected")
    before_status = dist.kyc_status
    dist.kyc_status = payload.status
    dist.kyc_verified_at = datetime.now(timezone.utc)
    dist.kyc_verified_by = principal.id
    dist.updated_by = principal.id
    async with AuditContext(
        db,
        actor_id=principal.id,
        entity="distributor",
        entity_id=dist.id,
        action="kyc_verify",
        request_id=request_id,
    ) as ctx:
        ctx.before = {"kyc_status": before_status}
        ctx.after = {
            "kyc_status": payload.status,
            "rejection_reason": payload.rejection_reason,
        }
    return DistributorOut.model_validate(dist)
