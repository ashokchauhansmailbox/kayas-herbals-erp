"""Customer self-service routes — `/me/profile`, `/me/addresses`, `/me/wallet`.

Any authenticated user can call these against their own records. No RBAC
permission required beyond authentication; the guard is that the endpoint
operates on `principal.id` from the JWT.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update

from app.deps import DbSession, RequestId, get_current_user
from app.models.customer import Address, CustomerProfile, Wallet
from app.schemas.customer import (
    AddressIn,
    AddressOut,
    AddressPatch,
    CustomerProfileIn,
    CustomerProfileOut,
    WalletOut,
)
from app.services.audit_service import AuditContext
from app.services.auth_service import Principal

router = APIRouter()


async def _upsert_profile(db, principal: Principal) -> CustomerProfile:
    row = (
        await db.execute(
            select(CustomerProfile).where(CustomerProfile.user_id == principal.id)
        )
    ).scalar_one_or_none()
    if row is None:
        row = CustomerProfile(
            user_id=principal.id,
            created_by=principal.id,
            updated_by=principal.id,
        )
        db.add(row)
        await db.flush()
    return row


async def _upsert_wallet(db, principal: Principal) -> Wallet:
    row = (
        await db.execute(select(Wallet).where(Wallet.user_id == principal.id))
    ).scalar_one_or_none()
    if row is None:
        row = Wallet(
            user_id=principal.id,
            created_by=principal.id,
            updated_by=principal.id,
        )
        db.add(row)
        await db.flush()
    return row


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------
@router.get("/profile", response_model=CustomerProfileOut)
async def get_my_profile(
    db: DbSession, principal: Principal = Depends(get_current_user)
) -> CustomerProfileOut:
    row = await _upsert_profile(db, principal)
    return CustomerProfileOut.model_validate(row)


@router.patch("/profile", response_model=CustomerProfileOut)
async def update_my_profile(
    payload: CustomerProfileIn,
    db: DbSession,
    request_id: RequestId,
    principal: Principal = Depends(get_current_user),
) -> CustomerProfileOut:
    row = await _upsert_profile(db, principal)
    changes = payload.model_dump(exclude_unset=True)
    for k, v in changes.items():
        setattr(row, k, v)
    row.updated_by = principal.id
    async with AuditContext(
        db,
        actor_id=principal.id,
        entity="customer_profile",
        entity_id=row.id,
        action="update",
        request_id=request_id,
    ) as ctx:
        ctx.before = {k: getattr(row, k) for k in changes}
        ctx.after = changes
    return CustomerProfileOut.model_validate(row)


# ---------------------------------------------------------------------------
# Addresses
# ---------------------------------------------------------------------------
@router.get("/addresses", response_model=list[AddressOut])
async def list_my_addresses(
    db: DbSession, principal: Principal = Depends(get_current_user)
) -> list[AddressOut]:
    rows = (
        await db.execute(
            select(Address)
            .where(
                Address.user_id == principal.id,
                Address.deleted_at.is_(None),
                Address.is_active.is_(True),
            )
            .order_by(Address.is_default.desc(), Address.created_at.desc())
        )
    ).scalars().all()
    return [AddressOut.model_validate(r) for r in rows]


async def _clear_defaults(db, user_id: UUID, label: str) -> None:
    await db.execute(
        update(Address)
        .where(
            Address.user_id == user_id,
            Address.label == label,
            Address.is_default.is_(True),
            Address.deleted_at.is_(None),
        )
        .values(is_default=False)
    )


@router.post("/addresses", response_model=AddressOut, status_code=201)
async def create_my_address(
    payload: AddressIn,
    db: DbSession,
    request_id: RequestId,
    principal: Principal = Depends(get_current_user),
) -> AddressOut:
    if payload.is_default:
        await _clear_defaults(db, principal.id, payload.label)
    addr = Address(
        user_id=principal.id,
        **payload.model_dump(),
        created_by=principal.id,
        updated_by=principal.id,
    )
    db.add(addr)
    await db.flush()
    async with AuditContext(
        db,
        actor_id=principal.id,
        entity="address",
        entity_id=addr.id,
        action="create",
        request_id=request_id,
    ) as ctx:
        ctx.before = None
        ctx.after = payload.model_dump(mode="json")
    return AddressOut.model_validate(addr)


@router.patch("/addresses/{address_id}", response_model=AddressOut)
async def update_my_address(
    address_id: UUID,
    payload: AddressPatch,
    db: DbSession,
    request_id: RequestId,
    principal: Principal = Depends(get_current_user),
) -> AddressOut:
    addr = (
        await db.execute(
            select(Address).where(
                Address.id == address_id,
                Address.user_id == principal.id,
                Address.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if addr is None:
        raise HTTPException(404, "Address not found")
    changes = payload.model_dump(exclude_unset=True)
    # If flipping to default, clear existing defaults at the same label first.
    if changes.get("is_default") is True:
        new_label = changes.get("label", addr.label)
        await _clear_defaults(db, principal.id, new_label)
    for k, v in changes.items():
        setattr(addr, k, v)
    addr.updated_by = principal.id
    async with AuditContext(
        db,
        actor_id=principal.id,
        entity="address",
        entity_id=addr.id,
        action="update",
        request_id=request_id,
    ) as ctx:
        ctx.before = {k: getattr(addr, k) for k in changes}
        ctx.after = changes
    return AddressOut.model_validate(addr)


@router.delete("/addresses/{address_id}", status_code=204)
async def delete_my_address(
    address_id: UUID,
    db: DbSession,
    request_id: RequestId,
    principal: Principal = Depends(get_current_user),
) -> None:
    addr = (
        await db.execute(
            select(Address).where(
                Address.id == address_id,
                Address.user_id == principal.id,
                Address.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if addr is None:
        raise HTTPException(404, "Address not found")
    addr.deleted_at = datetime.now(timezone.utc)
    addr.deleted_by = principal.id
    addr.is_active = False
    addr.is_default = False
    async with AuditContext(
        db,
        actor_id=principal.id,
        entity="address",
        entity_id=addr.id,
        action="delete",
        request_id=request_id,
    ) as ctx:
        ctx.before = {"is_active": True}
        ctx.after = {"is_active": False}


# ---------------------------------------------------------------------------
# Wallet
# ---------------------------------------------------------------------------
@router.get("/wallet", response_model=WalletOut)
async def get_my_wallet(
    db: DbSession, principal: Principal = Depends(get_current_user)
) -> WalletOut:
    wallet = await _upsert_wallet(db, principal)
    return WalletOut.model_validate(wallet)
