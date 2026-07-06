"""Idempotent seed script — runs on every startup / migration deploy.

Usage:
    python -m app.seeds.run

Seeds are additive: existing rows are not touched. Role→permission mapping
is fully replaced on each run for system roles (so adding a new permission
code takes effect without manual DB fiddling), but never for custom roles.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session_factory
from app.models.identity import Permission, Role, RolePermission
from app.models.master_data import (
    Brand,
    Category,
    CourierPartner,
    GstRate,
    HsnCode,
    PaymentTerm,
    TaxRule,
    Unit,
    Warehouse,
)
from app.seeds.master_data import (
    BRANDS,
    CATEGORIES,
    COURIER_PARTNERS,
    GST_RATES,
    HSN_CODES,
    PAYMENT_TERMS,
    TAX_RULES,
    UNITS,
    WAREHOUSES,
)
from app.seeds.permissions import PERMISSIONS
from app.seeds.roles import ROLES


async def _seed_permissions(db: AsyncSession) -> dict[str, Permission]:
    by_code: dict[str, Permission] = {}
    existing = {p.code: p for p in (await db.execute(select(Permission))).scalars()}
    for code, module, description in PERMISSIONS:
        row = existing.get(code)
        if row is None:
            row = Permission(code=code, module=module, description=description)
            db.add(row)
        else:
            row.module = module
            row.description = description
        by_code[code] = row
    await db.flush()
    return by_code


def _role_from_spec(spec: dict, existing: Role | None) -> tuple[Role, bool]:
    """Upsert helper — returns (role, is_new). Updates existing in place."""
    code = str(spec["code"])
    name = str(spec["name"])
    description = str(spec.get("description") or "")
    is_system = bool(spec.get("is_system", False))
    if existing is None:
        return Role(
            code=code, name=name, description=description, is_system=is_system
        ), True
    existing.name = name
    existing.description = description
    existing.is_system = is_system
    return existing, False


def _validate_perm_codes(role_code: str, perms_list: object) -> list[str]:
    if not isinstance(perms_list, list):
        raise TypeError(f"role {role_code!r}: permissions must be a list")
    for pcode in perms_list:
        if not isinstance(pcode, str):
            raise TypeError(
                f"Non-string permission code in role {role_code!r}: {pcode!r}"
            )
    return perms_list


async def _remap_role_perms(
    db: AsyncSession, role: Role, perms_list: list[str], perms: dict[str, Permission]
) -> None:
    await db.execute(
        delete(RolePermission).where(RolePermission.role_id == role.id)
    )
    for pcode in perms_list:
        perm = perms.get(pcode)
        if perm is None:
            raise ValueError(
                f"Unknown permission code in role {role.code!r}: {pcode!r}"
            )
        db.add(RolePermission(role_id=role.id, permission_id=perm.id))


async def _seed_roles(
    db: AsyncSession, perms: dict[str, Permission]
) -> dict[str, Role]:
    by_code: dict[str, Role] = {}
    existing = {r.code: r for r in (await db.execute(select(Role))).scalars()}
    for spec in ROLES:
        row, is_new = _role_from_spec(spec, existing.get(str(spec["code"])))
        if is_new:
            db.add(row)
        by_code[str(spec["code"])] = row
    await db.flush()

    # Re-map system roles' permissions fully; leave custom roles alone.
    for spec in ROLES:
        role = by_code[str(spec["code"])]
        if not role.is_system:
            continue
        codes = _validate_perm_codes(role.code, spec.get("permissions") or [])
        await _remap_role_perms(db, role, codes, perms)
    await db.flush()
    return by_code


async def _seed_units(db: AsyncSession) -> None:
    existing = {u.code for u in (await db.execute(select(Unit))).scalars()}
    for spec in UNITS:
        if spec["code"] not in existing:
            db.add(Unit(**spec))
    await db.flush()


async def _seed_gst_rates(db: AsyncSession) -> dict[Decimal, GstRate]:
    existing = {g.rate: g for g in (await db.execute(select(GstRate))).scalars()}
    out: dict[Decimal, GstRate] = dict(existing)
    for spec in GST_RATES:
        rate = spec["rate"]
        if rate not in out:
            row = GstRate(**spec)
            db.add(row)
            out[rate] = row
    await db.flush()
    return out


async def _seed_hsn_codes(
    db: AsyncSession, gst_by_rate: dict[Decimal, GstRate]
) -> None:
    existing = {h.code for h in (await db.execute(select(HsnCode))).scalars()}
    for spec in HSN_CODES:
        code = spec["code"]
        if code in existing:
            continue
        gst = gst_by_rate.get(spec["gst_rate"])
        db.add(
            HsnCode(
                code=code,
                description=spec.get("description"),
                default_gst_rate_id=gst.id if gst else None,
            )
        )
    await db.flush()


async def _seed_categories(db: AsyncSession) -> None:
    existing = {c.slug for c in (await db.execute(select(Category))).scalars()}
    for spec in CATEGORIES:
        if spec["slug"] not in existing:
            db.add(Category(**spec))
    await db.flush()


async def _seed_brands(db: AsyncSession) -> None:
    existing = {b.slug for b in (await db.execute(select(Brand))).scalars()}
    for spec in BRANDS:
        if spec["slug"] not in existing:
            db.add(Brand(**spec))
    await db.flush()


async def _seed_warehouses(db: AsyncSession) -> None:
    existing = {w.code for w in (await db.execute(select(Warehouse))).scalars()}
    for spec in WAREHOUSES:
        if spec["code"] not in existing:
            db.add(Warehouse(**spec))
    await db.flush()


async def _seed_payment_terms(db: AsyncSession) -> None:
    existing = {p.code for p in (await db.execute(select(PaymentTerm))).scalars()}
    for spec in PAYMENT_TERMS:
        if spec["code"] not in existing:
            db.add(PaymentTerm(**spec))
    await db.flush()


async def _seed_tax_rules(db: AsyncSession) -> None:
    existing = {t.code for t in (await db.execute(select(TaxRule))).scalars()}
    for spec in TAX_RULES:
        if spec["code"] not in existing:
            db.add(TaxRule(**spec))
    await db.flush()


async def _seed_courier_partners(db: AsyncSession) -> None:
    existing = {c.code for c in (await db.execute(select(CourierPartner))).scalars()}
    for spec in COURIER_PARTNERS:
        if spec["code"] not in existing:
            db.add(CourierPartner(**spec))
    await db.flush()


async def run() -> dict[str, int]:
    """Run all seed steps in one transaction; return per-entity insert counts."""
    factory = get_session_factory()
    async with factory() as db:
        perms = await _seed_permissions(db)
        await _seed_roles(db, perms)
        gst_by_rate = await _seed_gst_rates(db)
        await _seed_units(db)
        await _seed_hsn_codes(db, gst_by_rate)
        await _seed_categories(db)
        await _seed_brands(db)
        await _seed_warehouses(db)
        await _seed_payment_terms(db)
        await _seed_tax_rules(db)
        await _seed_courier_partners(db)
        await db.commit()

        # Return counts after commit — a small observability aid.
        counts = {}
        for label, model in (
            ("permissions", Permission),
            ("roles", Role),
            ("units", Unit),
            ("gst_rates", GstRate),
            ("hsn_codes", HsnCode),
            ("categories", Category),
            ("brands", Brand),
            ("warehouses", Warehouse),
            ("payment_terms", PaymentTerm),
            ("tax_rules", TaxRule),
            ("courier_partners", CourierPartner),
        ):
            counts[label] = (
                (await db.execute(select(model))).scalars().unique().all().__len__()
            )
        return counts


def main() -> None:
    counts = asyncio.run(run())
    for k, v in counts.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
