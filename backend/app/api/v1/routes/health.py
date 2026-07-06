"""Health / liveness endpoints.

`/api/v1/health/live`  → process is up (no dependencies).
`/api/v1/health/ready` → DB reachable + `SELECT 1` succeeds.
`/api/v1/health/db`    → alembic head + row counts (Sprint 1.1 verification aid).
"""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import get_engine

router = APIRouter(prefix="/health")


@router.get("/live")
async def live() -> dict:
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict:
    engine = get_engine()
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        _ = result.scalar_one()
    return {"status": "ok", "db": "up"}


@router.get("/db")
async def db_status() -> dict:
    """Sprint 1.1 helper: report current Alembic revision + table counts."""
    engine = get_engine()
    async with engine.connect() as conn:
        rev = (
            await conn.execute(text("SELECT version_num FROM alembic_version"))
        ).scalar_one_or_none()
        tables = (
            (
                await conn.execute(
                    text(
                        "SELECT tablename FROM pg_tables "
                        "WHERE schemaname = 'public' ORDER BY tablename"
                    )
                )
            )
            .scalars()
            .all()
        )
    return {"alembic_revision": rev, "tables": list(tables), "table_count": len(tables)}
