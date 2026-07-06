"""Sprint 1.4 — Customer self-service route tests (`/me/*`)."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_me_profile_auto_provisions(client, mint):
    tu = await mint(role_codes=["customer"])
    h = {"Authorization": f"Bearer {tu.token}"}
    r = await client.get("/api/v1/me/profile", headers=h)
    assert r.status_code == 200
    assert r.json()["user_id"] == str(tu.id)
    # patch
    r = await client.patch(
        "/api/v1/me/profile",
        headers=h,
        json={"phone": "+91 9876543210", "gender": "female", "marketing_opt_in": True},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["phone"] == "+91 9876543210"
    assert body["gender"] == "female"
    assert body["marketing_opt_in"] is True


@pytest.mark.asyncio
async def test_me_profile_rejects_invalid_gender(client, mint):
    tu = await mint(role_codes=["customer"])
    h = {"Authorization": f"Bearer {tu.token}"}
    r = await client.patch(
        "/api/v1/me/profile", headers=h, json={"gender": "unicorn"}
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_me_addresses_crud_and_default_invariant(client, mint):
    tu = await mint(role_codes=["customer"])
    h = {"Authorization": f"Bearer {tu.token}"}
    # start empty
    r = await client.get("/api/v1/me/addresses", headers=h)
    assert r.json() == []
    # first default shipping
    a1 = {
        "recipient_name": "Ashok",
        "line1": "123 Green St",
        "city": "Bengaluru",
        "state": "KA",
        "pincode": "560001",
        "is_default": True,
    }
    r = await client.post("/api/v1/me/addresses", headers=h, json=a1)
    assert r.status_code == 201, r.text
    aid1 = r.json()["id"]
    # second default shipping -> the previous one must lose its default
    a2 = {**a1, "recipient_name": "Ashok #2", "line1": "456 Rose Ave"}
    r = await client.post("/api/v1/me/addresses", headers=h, json=a2)
    assert r.status_code == 201
    aid2 = r.json()["id"]
    r = await client.get("/api/v1/me/addresses", headers=h)
    ordered = r.json()
    assert len(ordered) == 2
    defaults = [x for x in ordered if x["is_default"]]
    assert len(defaults) == 1
    assert defaults[0]["id"] == aid2
    # patch first back to default
    r = await client.patch(
        f"/api/v1/me/addresses/{aid1}", headers=h, json={"is_default": True}
    )
    assert r.status_code == 200
    r = await client.get("/api/v1/me/addresses", headers=h)
    defaults = [x for x in r.json() if x["is_default"]]
    assert len(defaults) == 1
    assert defaults[0]["id"] == aid1
    # soft delete
    r = await client.delete(f"/api/v1/me/addresses/{aid2}", headers=h)
    assert r.status_code == 204
    r = await client.get("/api/v1/me/addresses", headers=h)
    assert len(r.json()) == 1
    assert r.json()[0]["id"] == aid1


@pytest.mark.asyncio
async def test_me_addresses_isolated_across_users(client, mint):
    a = await mint(role_codes=["customer"])
    b = await mint(role_codes=["customer"])
    ha = {"Authorization": f"Bearer {a.token}"}
    hb = {"Authorization": f"Bearer {b.token}"}
    await client.post(
        "/api/v1/me/addresses",
        headers=ha,
        json={
            "recipient_name": "A",
            "line1": "L1",
            "city": "C",
            "state": "S",
            "pincode": "111111",
        },
    )
    r = await client.get("/api/v1/me/addresses", headers=hb)
    assert r.json() == []


@pytest.mark.asyncio
async def test_me_wallet_auto_provisions_zero_balance(client, mint):
    tu = await mint(role_codes=["customer"])
    h = {"Authorization": f"Bearer {tu.token}"}
    r = await client.get("/api/v1/me/wallet", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["user_id"] == str(tu.id)
    assert body["currency"] == "INR"
    assert body["balance"] == "0.00"
    assert body["is_active"] is True


@pytest.mark.asyncio
async def test_me_requires_authentication(client):
    r = await client.get("/api/v1/me/profile")
    assert r.status_code == 401
    r = await client.get("/api/v1/me/wallet")
    assert r.status_code == 401
    r = await client.get("/api/v1/me/addresses")
    assert r.status_code == 401
