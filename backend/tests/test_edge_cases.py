"""Edge-case + regression tests added during the Sprint 1.3 Quality Gate.

Covers input-validation boundaries, permission boundaries, and pagination
edge cases that were not caught by the module-specific suites.
"""
from __future__ import annotations

import uuid

import pytest


@pytest.mark.asyncio
async def test_pagination_page_zero_rejected(client, mint):
    admin = await mint(role_codes=["super_admin"])
    r = await client.get(
        "/api/v1/users?page=0",
        headers={"Authorization": f"Bearer {admin.token}"},
    )
    assert r.status_code == 422  # FastAPI validation error


@pytest.mark.asyncio
async def test_pagination_page_size_over_limit_rejected(client, mint):
    admin = await mint(role_codes=["super_admin"])
    r = await client.get(
        "/api/v1/audit/logs?page_size=10000",
        headers={"Authorization": f"Bearer {admin.token}"},
    )
    # page_size is now bounded to <=200 (Sprint 1.3 QG fix); large values → 422.
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_get_user_by_invalid_uuid_returns_422(client, mint):
    admin = await mint(role_codes=["super_admin"])
    r = await client.get(
        "/api/v1/users/not-a-uuid",
        headers={"Authorization": f"Bearer {admin.token}"},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_get_user_by_unknown_uuid_returns_404(client, mint):
    admin = await mint(role_codes=["super_admin"])
    unknown = uuid.uuid4()
    r = await client.get(
        f"/api/v1/users/{unknown}",
        headers={"Authorization": f"Bearer {admin.token}"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_role_duplicate_code_rejected(client, mint):
    admin = await mint(role_codes=["super_admin"])
    h = {"Authorization": f"Bearer {admin.token}"}
    unique = f"dup-{uuid.uuid4().hex[:6]}"
    r1 = await client.post(
        "/api/v1/roles",
        headers=h,
        json={"code": unique, "name": "R", "permissions": []},
    )
    assert r1.status_code == 201
    r2 = await client.post(
        "/api/v1/roles",
        headers=h,
        json={"code": unique, "name": "R2", "permissions": []},
    )
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_role_unknown_permission_rejected(client, mint):
    admin = await mint(role_codes=["super_admin"])
    r = await client.post(
        "/api/v1/roles",
        headers={"Authorization": f"Bearer {admin.token}"},
        json={"code": f"badperm-{uuid.uuid4().hex[:6]}", "name": "R", "permissions": ["doesnotexist"]},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_invitation_unknown_role_rejected(client, mint):
    admin = await mint(role_codes=["super_admin"])
    r = await client.post(
        "/api/v1/invitations",
        headers={"Authorization": f"Bearer {admin.token}"},
        json={"email": "candidate@example.com", "role_code": "not-a-real-role"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_invitation_invalid_email_rejected(client, mint):
    admin = await mint(role_codes=["super_admin"])
    r = await client.post(
        "/api/v1/invitations",
        headers={"Authorization": f"Bearer {admin.token}"},
        json={"email": "not-an-email", "role_code": "customer"},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_error_envelope_includes_request_id(client):
    r = await client.get("/api/v1/audit/logs")
    assert r.status_code == 401
    body = r.json()
    assert "error" in body and "request_id" in body["error"]
    assert body["error"]["request_id"] is not None and body["error"]["request_id"] != ""


@pytest.mark.asyncio
async def test_list_users_batch_query_avoids_n_plus_one(client, mint, db):
    """Regression: /users list must fetch role codes in ONE extra query, not N."""
    from sqlalchemy import select

    from app.models.identity import Role, User, UserRole

    admin = await mint(role_codes=["super_admin"])
    # add 5 users with 1 role each
    role = (await db.execute(select(Role).where(Role.code == "customer"))).scalar_one()
    for _ in range(5):
        u = User(id=uuid.uuid4(), email=f"nplus1-{uuid.uuid4().hex[:6]}@example.com", status="active")
        db.add(u)
        await db.flush()
        db.add(UserRole(user_id=u.id, role_id=role.id))
    await db.commit()

    # Count queries executed by /users?page_size=25.
    from sqlalchemy import event

    engine = db.bind
    counter = {"n": 0}

    def _before(conn, cursor, statement, parameters, context, executemany):
        counter["n"] += 1

    event.listen(engine.sync_engine, "before_cursor_execute", _before)
    try:
        r = await client.get(
            "/api/v1/users?page_size=25",
            headers={"Authorization": f"Bearer {admin.token}"},
        )
        assert r.status_code == 200
        # Reasonable ceiling: auth + user load + roles + count + users + batch roles +
        # activity log + session upsert < 20. If we regress into N+1 with 6 rows,
        # the count balloons past 25.
        assert counter["n"] < 25, f"suspected N+1: {counter['n']} queries"
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", _before)
