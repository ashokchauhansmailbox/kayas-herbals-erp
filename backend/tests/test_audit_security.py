"""Audit + activity logging tests + OWASP-adjacent security scenarios."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.models.identity import ActivityLog, AuditLog


@pytest.mark.asyncio
async def test_role_update_writes_audit_log(client, mint, db):
    admin = await mint(role_codes=["super_admin"])
    h = {"Authorization": f"Bearer {admin.token}"}
    # create a custom role
    r = await client.post(
        "/api/v1/roles",
        headers=h,
        json={"code": "audit-role-1", "name": "R1", "permissions": []},
    )
    assert r.status_code == 201
    role_id = r.json()["id"]
    # update it
    r = await client.patch(
        "/api/v1/roles/audit-role-1", headers=h, json={"name": "R1-renamed"}
    )
    assert r.status_code == 200
    # audit row must exist
    rows = (
        (
            await db.execute(
                select(AuditLog).where(
                    AuditLog.entity == "role", AuditLog.entity_id == uuid.UUID(role_id)
                )
            )
        )
        .scalars()
        .all()
    )
    actions = {r.action for r in rows}
    assert "create" in actions and "update" in actions
    # diff should be non-null on the update row
    update_rows = [r for r in rows if r.action == "update"]
    assert update_rows[0].before is not None
    assert update_rows[0].after is not None


@pytest.mark.asyncio
async def test_me_writes_activity_log(client, mint, db):
    tu = await mint(role_codes=["customer"])
    await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tu.token}"})
    rows = (
        (await db.execute(select(ActivityLog).where(ActivityLog.actor_id == tu.id)))
        .scalars()
        .all()
    )
    assert any(r.event == "auth.me" for r in rows)


@pytest.mark.asyncio
async def test_audit_endpoint_paginates(client, mint):
    admin = await mint(role_codes=["super_admin"])
    h = {"Authorization": f"Bearer {admin.token}"}
    r = await client.get("/api/v1/audit/logs?page=1&page_size=5", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert "items" in data and "total" in data and data["page_size"] == 5


# ---------------------------------------------------------------------------
# OWASP-adjacent security scenarios
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_owasp_sql_injection_input_is_parameterised(client, mint):
    """A2021-A03 Injection — search string with SQL metacharacters must not error out."""
    admin = await mint(role_codes=["super_admin"])
    h = {"Authorization": f"Bearer {admin.token}"}
    r = await client.get("/api/v1/users?q=%27+OR+1%3D1--", headers=h)
    assert r.status_code == 200
    # No 500. The list still returns a valid Page envelope.
    body = r.json()
    assert "items" in body


@pytest.mark.asyncio
async def test_owasp_idor_customer_cannot_read_another_users_detail(client, mint):
    """A2021-A01 BOLA/IDOR — customer requesting another user's detail = 403."""
    a = await mint(role_codes=["customer"])
    b = await mint(role_codes=["customer"])
    r = await client.get(
        f"/api/v1/users/{b.id}", headers={"Authorization": f"Bearer {a.token}"}
    )
    # customer role doesn't have users.read → 403
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_owasp_broken_auth_missing_bearer(client):
    """A2021-A07 Identification and Authentication Failures — missing bearer = 401."""
    r = await client.get("/api/v1/audit/logs")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_owasp_broken_access_missing_permission(client, mint):
    """A2021-A01 — user with a role but missing THE specific permission = 403."""
    tu = await mint(role_codes=["marketing_manager"])
    r = await client.delete(
        "/api/v1/roles/customer",
        headers={"Authorization": f"Bearer {tu.token}"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_owasp_error_envelope_does_not_leak_internals(client, mint):
    """Error envelope is stable across error types — no stack trace, no query string."""
    tu = await mint(role_codes=["customer"])
    r = await client.get(
        "/api/v1/users/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {tu.token}"},
    )
    body = r.json()
    assert r.status_code == 403 or r.status_code == 404
    assert "error" in body
    assert "traceback" not in str(body).lower()
    assert "select" not in str(body).lower()  # no SQL leakage


@pytest.mark.asyncio
async def test_owasp_wrong_signing_algorithm_rejected(client):
    """A2021-A02 Cryptographic Failures — 'none' algorithm rejected."""
    import base64
    import json

    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "none", "typ": "JWT"}).encode()
    ).rstrip(b"=")
    payload = base64.urlsafe_b64encode(
        json.dumps(
            {"sub": str(uuid.uuid4()), "aud": "authenticated", "exp": 9999999999}
        ).encode()
    ).rstrip(b"=")
    token = f"{header.decode()}.{payload.decode()}."
    r = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_seed_is_idempotent():
    """Running seed twice does not duplicate rows."""
    from app.seeds.run import run

    a = await run()
    b = await run()
    assert a == b
