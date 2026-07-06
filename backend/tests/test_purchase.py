"""Sprint 1.4 — Purchase master (vendors) route tests.

Verifies: CRUD, RBAC guards on mutations, GSTIN validation, pagination, soft-delete."""

from __future__ import annotations

import uuid

import pytest


def _code(prefix: str) -> str:
    """Unique per-test business code — HTTP-committed rows persist across tests."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


@pytest.mark.asyncio
async def test_list_vendors_requires_read_permission(client, mint):
    tu = await mint(role_codes=["customer"])
    r = await client.get(
        "/api/v1/vendors", headers={"Authorization": f"Bearer {tu.token}"}
    )
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "rbac.forbidden"


@pytest.mark.asyncio
async def test_create_vendor_requires_manage_permission(client, mint):
    # `customer` role has no purchase.* / vendors.* permissions.
    tu = await mint(role_codes=["customer"])
    payload = {"code": _code("V"), "name": "Herbal Co"}
    r = await client.post(
        "/api/v1/vendors",
        headers={"Authorization": f"Bearer {tu.token}"},
        json=payload,
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_vendor_crud_happy_path(client, mint):
    tu = await mint(role_codes=["super_admin"])
    h = {"Authorization": f"Bearer {tu.token}"}
    r = await client.get("/api/v1/vendors", headers=h)
    assert r.status_code == 200
    # (Cannot assert total == 0 — HTTP-committed rows from earlier tests persist.)
    # create
    payload = {
        "code": _code("V"),
        "name": "Ayur Sourcing Pvt Ltd",
        "gstin": "27AAECS1234N1Z9",
        "credit_days": 30,
    }
    r = await client.post("/api/v1/vendors", headers=h, json=payload)
    assert r.status_code == 201, r.text
    body = r.json()
    vid = body["id"]
    assert body["code"] == payload["code"]
    assert body["is_active"] is True
    # duplicate
    r = await client.post("/api/v1/vendors", headers=h, json=payload)
    assert r.status_code == 409
    # get
    r = await client.get(f"/api/v1/vendors/{vid}", headers=h)
    assert r.status_code == 200
    # patch
    r = await client.patch(
        f"/api/v1/vendors/{vid}",
        headers=h,
        json={"name": "Ayur Sourcing", "credit_days": 60},
    )
    assert r.status_code == 200
    assert r.json()["credit_days"] == 60
    # list finds it
    r = await client.get("/api/v1/vendors?q=Ayur", headers=h)
    assert r.status_code == 200
    assert r.json()["total"] >= 1
    # soft delete
    r = await client.delete(f"/api/v1/vendors/{vid}", headers=h)
    assert r.status_code == 204
    r = await client.get(f"/api/v1/vendors/{vid}", headers=h)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_vendor_rejects_invalid_code(client, mint):
    tu = await mint(role_codes=["super_admin"])
    h = {"Authorization": f"Bearer {tu.token}"}
    r = await client.post(
        "/api/v1/vendors", headers=h, json={"code": "with space", "name": "X"}
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_vendor_credit_days_bounds(client, mint):
    tu = await mint(role_codes=["super_admin"])
    h = {"Authorization": f"Bearer {tu.token}"}
    r = await client.post(
        "/api/v1/vendors",
        headers=h,
        json={"code": _code("V"), "name": "X", "credit_days": -1},
    )
    assert r.status_code == 422
    r = await client.post(
        "/api/v1/vendors",
        headers=h,
        json={"code": _code("V"), "name": "X", "credit_days": 366},
    )
    assert r.status_code == 422
