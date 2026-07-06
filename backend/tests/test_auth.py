"""Authentication tests — token verification, expiry, audience, signature."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_me_requires_bearer(client):
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401
    body = r.json()["error"]
    assert body["code"] == "auth.missing_bearer"


@pytest.mark.asyncio
async def test_me_success(client, mint):
    tu = await mint(role_codes=["customer"])
    r = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tu.token}"}
    )
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == tu.email
    assert data["status"] == "active"
    assert "customer" in data["roles"]
    assert "products.read" in data["permissions"]


@pytest.mark.asyncio
async def test_expired_token_rejected(client, mint):
    tu = await mint(role_codes=["customer"], ttl_seconds=-10)
    r = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tu.token}"}
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "auth.token_expired"


@pytest.mark.asyncio
async def test_wrong_audience_rejected(client, mint):
    tu = await mint(role_codes=["customer"], aud="wrong-audience")
    r = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tu.token}"}
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "auth.invalid_audience"


@pytest.mark.asyncio
async def test_tampered_signature_rejected(client, mint):
    tu = await mint(role_codes=["customer"])
    tampered = tu.token[:-4] + "AAAA"
    r = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tampered}"}
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] in {"auth.invalid_signature", "auth.invalid_token"}


@pytest.mark.asyncio
async def test_wrong_signing_secret_rejected(client, mint):
    tu = await mint(role_codes=["customer"], secret="not-the-real-secret-but-32-bytes-long-x")
    r = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tu.token}"}
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_malformed_authorization_rejected(client):
    r = await client.get("/api/v1/auth/me", headers={"Authorization": "Token abc.def"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "auth.malformed_bearer"


@pytest.mark.asyncio
async def test_logout_revokes_session(client, mint):
    tu = await mint(role_codes=["customer"])
    headers = {"Authorization": f"Bearer {tu.token}"}
    # 1st /me to record the session
    r = await client.get("/api/v1/auth/me", headers=headers)
    assert r.status_code == 200
    # logout
    r = await client.post("/api/v1/auth/logout", headers=headers)
    assert r.status_code == 204
    # subsequent request must fail with session_revoked
    r = await client.get("/api/v1/auth/me", headers=headers)
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "auth.session_revoked"


@pytest.mark.asyncio
async def test_suspended_user_rejected(client, mint):
    tu = await mint(role_codes=["customer"], status="suspended")
    r = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tu.token}"}
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "auth.user_suspended"


@pytest.mark.asyncio
async def test_missing_sub_rejected(client, mint):
    # Craft a token with no sub — mint requires sub, so instead we tamper with the
    # subject to an invalid UUID.
    from app.core.security import mint_token

    token = mint_token(sub="not-a-uuid")
    r = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "auth.invalid_subject"


@pytest.mark.asyncio
async def test_sessions_lists_user_sessions(client, mint):
    tu = await mint(role_codes=["customer"])
    h = {"Authorization": f"Bearer {tu.token}"}
    await client.get("/api/v1/auth/me", headers=h)
    r = await client.get("/api/v1/auth/sessions", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert any(s["jti"] for s in body)
