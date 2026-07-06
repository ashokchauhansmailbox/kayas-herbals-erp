"""RBAC + authorization tests.

Verifies:
    * Every permission code is reachable by at least one role that carries it.
    * Missing permission → 403 with rbac.forbidden.
    * Effective permission set for a role matches its seed spec.
    * Cross-role isolation (customer cannot read audit).
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models.identity import Permission, Role, RolePermission
from app.seeds.roles import ROLES


@pytest.mark.asyncio
async def test_every_seeded_permission_is_installed(db):
    from app.seeds.permissions import PERMISSIONS

    codes = {p.code for p in (await db.execute(select(Permission))).scalars()}
    for c, _, _ in PERMISSIONS:
        assert c in codes, f"seed permission missing from DB: {c}"


@pytest.mark.asyncio
async def test_every_seeded_role_has_expected_permissions(db):
    for spec in ROLES:
        code = spec["code"]
        role = (await db.execute(select(Role).where(Role.code == code))).scalar_one()
        actual = set(
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
        expected = set(spec["permissions"])  # type: ignore[index]
        assert (
            actual == expected
        ), f"role {code}: unexpected drift.\nmissing={expected-actual}\nextra={actual-expected}"


@pytest.mark.asyncio
async def test_customer_cannot_read_audit(client, mint):
    tu = await mint(role_codes=["customer"])
    r = await client.get(
        "/api/v1/audit/logs", headers={"Authorization": f"Bearer {tu.token}"}
    )
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "rbac.forbidden"
    assert r.json()["error"]["details"]["permission"] == "audit.read"


@pytest.mark.asyncio
async def test_customer_cannot_list_users(client, mint):
    tu = await mint(role_codes=["customer"])
    r = await client.get(
        "/api/v1/users", headers={"Authorization": f"Bearer {tu.token}"}
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_super_admin_reads_users(client, mint):
    tu = await mint(role_codes=["super_admin"])
    r = await client.get(
        "/api/v1/users", headers={"Authorization": f"Bearer {tu.token}"}
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_super_admin_can_create_custom_role(client, mint):
    tu = await mint(role_codes=["super_admin"])
    r = await client.post(
        "/api/v1/roles",
        headers={"Authorization": f"Bearer {tu.token}"},
        json={
            "code": "custom-role-1",
            "name": "Custom Role 1",
            "permissions": ["products.read", "orders.read"],
        },
    )
    assert r.status_code == 201
    assert r.json()["is_system"] is False
    assert set(r.json()["permissions"]) == {"products.read", "orders.read"}


@pytest.mark.asyncio
async def test_super_admin_cannot_delete_system_role(client, mint):
    tu = await mint(role_codes=["super_admin"])
    r = await client.delete(
        "/api/v1/roles/super_admin",
        headers={"Authorization": f"Bearer {tu.token}"},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_permissions_catalog_readable_by_role_holder(client, mint):
    tu = await mint(role_codes=["super_admin"])
    r = await client.get(
        "/api/v1/permissions",
        headers={"Authorization": f"Bearer {tu.token}"},
    )
    assert r.status_code == 200
    codes = {row["code"] for row in r.json()}
    assert "orders.refund" in codes
    assert "audit.read" in codes


@pytest.mark.asyncio
async def test_marketing_manager_cannot_manage_users(client, mint):
    tu = await mint(role_codes=["marketing_manager"])
    r = await client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {tu.token}"},
    )
    assert r.status_code == 403
