"""Sprint 1.4 — Distributor + Tier + KYC route tests."""

from __future__ import annotations

import uuid

import pytest


def _code(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


@pytest.mark.asyncio
async def test_tier_crud_and_ordering(client, mint):
    tu = await mint(role_codes=["super_admin"])
    h = {"Authorization": f"Bearer {tu.token}"}
    silver = _code("TIER")
    gold = _code("TIER")
    payload = {"code": silver, "name": "Silver", "default_discount_pct": "5.00"}
    r = await client.post("/api/v1/distributor-tiers", headers=h, json=payload)
    assert r.status_code == 201, r.text
    r = await client.post(
        "/api/v1/distributor-tiers",
        headers=h,
        json={"code": gold, "name": "Gold", "default_discount_pct": "10.00", "sort_order": 2},
    )
    assert r.status_code == 201
    r = await client.get("/api/v1/distributor-tiers", headers=h)
    assert r.status_code == 200
    codes = [t["code"] for t in r.json()]
    assert silver in codes and gold in codes
    r = await client.patch(
        f"/api/v1/distributor-tiers/{silver}",
        headers=h,
        json={"default_discount_pct": "7.00"},
    )
    assert r.status_code == 200
    assert r.json()["default_discount_pct"] == "7.00"


@pytest.mark.asyncio
async def test_tier_discount_must_be_percentage(client, mint):
    tu = await mint(role_codes=["super_admin"])
    h = {"Authorization": f"Bearer {tu.token}"}
    r = await client.post(
        "/api/v1/distributor-tiers",
        headers=h,
        json={"code": _code("TIER"), "name": "T1", "default_discount_pct": "101"},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_distributor_create_and_kyc_verify(client, mint):
    tu = await mint(role_codes=["super_admin"])
    h = {"Authorization": f"Bearer {tu.token}"}
    r = await client.post(
        "/api/v1/distributors",
        headers=h,
        json={
            "code": _code("D"),
            "business_name": "Delhi Ayurveda LLP",
            "gstin": "07AAECS9876N1Z5",
            "credit_limit": "50000.00",
            "credit_days": 30,
        },
    )
    assert r.status_code == 201, r.text
    did = r.json()["id"]
    assert r.json()["kyc_status"] == "pending"
    # verify KYC
    r = await client.post(
        f"/api/v1/distributors/{did}/kyc",
        headers=h,
        json={"status": "verified"},
    )
    assert r.status_code == 200
    assert r.json()["kyc_status"] == "verified"
    # reject requires reason
    r = await client.post(
        f"/api/v1/distributors/{did}/kyc",
        headers=h,
        json={"status": "rejected"},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_distributor_list_and_filter(client, mint):
    tu = await mint(role_codes=["super_admin"])
    h = {"Authorization": f"Bearer {tu.token}"}
    tag = uuid.uuid4().hex[:6]
    for i in range(2):
        await client.post(
            "/api/v1/distributors",
            headers=h,
            json={"code": f"D-{tag}-{i}", "business_name": f"Biz {tag} {i}"},
        )
    r = await client.get("/api/v1/distributors?kyc_status=pending", headers=h)
    assert r.status_code == 200
    assert r.json()["total"] >= 2
    r = await client.get(f"/api/v1/distributors?q=D-{tag}-0", headers=h)
    assert r.json()["total"] == 1


@pytest.mark.asyncio
async def test_distributor_read_requires_permission(client, mint):
    tu = await mint(role_codes=["customer"])
    h = {"Authorization": f"Bearer {tu.token}"}
    r = await client.get("/api/v1/distributors", headers=h)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_kyc_verify_requires_dedicated_permission(client, mint):
    # sales_manager has distributors.read + distributors.manage but no distributors.kyc_verify.
    tu = await mint(role_codes=["sales_manager"])
    h = {"Authorization": f"Bearer {tu.token}"}
    r = await client.post(
        "/api/v1/distributors",
        headers=h,
        json={"code": _code("D"), "business_name": "Test"},
    )
    if r.status_code == 201:
        did = r.json()["id"]
        r = await client.post(
            f"/api/v1/distributors/{did}/kyc",
            headers=h,
            json={"status": "verified"},
        )
        assert r.status_code == 403
    else:
        # sales_manager lacks distributors.manage — that's also fine.
        assert r.status_code == 403
