"""Shared pytest fixtures for all Sprint 1.x tests."""

from __future__ import annotations

import os
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator, Iterable

import pytest
import pytest_asyncio
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")


def _base_sync_url() -> str | None:
    url = os.environ.get("DATABASE_URL_TEST_SYNC") or os.environ.get(
        "DATABASE_URL_SYNC"
    )
    if not url:
        return None
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
    return url


def _admin_url_and_dbname(sync_url: str) -> tuple[str, str]:
    prefix, _, dbname = sync_url.rpartition("/")
    return f"{prefix}/postgres", dbname


def _ensure_db(admin_url: str, dbname: str) -> None:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

    dsn = admin_url.replace("postgresql+psycopg2://", "postgresql://", 1)
    conn = psycopg2.connect(dsn)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
        if cur.fetchone() is None:
            cur.execute(f'CREATE DATABASE "{dbname}"')
    conn.close()


@pytest.fixture(scope="session")
def sync_db_url(worker_id: str) -> str:
    base = _base_sync_url()
    if not base:
        pytest.skip("DATABASE_URL_TEST_SYNC / DATABASE_URL_SYNC not configured")
    admin_url, base_db = _admin_url_and_dbname(base)
    suffix = "" if worker_id == "master" else f"_{worker_id}"
    dbname = f"{base_db}{suffix}"
    _ensure_db(admin_url, dbname)
    return f"{admin_url.rsplit('/', 1)[0]}/{dbname}"


@pytest.fixture(scope="session")
def async_db_url(sync_db_url: str) -> str:
    return sync_db_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)


@pytest.fixture(autouse=True, scope="session")
def _apply_migrations_and_seed(sync_db_url: str, async_db_url: str) -> None:
    """Run alembic + seed synchronously (via subprocess) so no async loop is bound."""
    subprocess.run(
        ["alembic", "-x", f"db_url={sync_db_url}", "upgrade", "head"],
        cwd=BACKEND_DIR,
        check=True,
        capture_output=True,
    )
    # Set runtime engine URL so the FastAPI app hits the same DB.
    os.environ["DATABASE_URL"] = async_db_url
    from app.core.config import get_settings

    get_settings.cache_clear()  # type: ignore[attr-defined]

    # Seed via subprocess (own event loop) so we do not attach connections to
    # any long-lived loop.
    r = subprocess.run(
        ["python", "-m", "app.seeds.run"],
        cwd=BACKEND_DIR,
        env={**os.environ, "DATABASE_URL": async_db_url},
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:  # pragma: no cover — surfaces seed errors quickly
        raise RuntimeError(f"Seed failed: {r.stderr}")


# ---------------------------------------------------------------------------
# Function-scoped async fixtures — each test gets a fresh engine + client
# ---------------------------------------------------------------------------
@dataclass
class TestUser:
    id: uuid.UUID
    email: str
    token: str


@pytest_asyncio.fixture(scope="session")
async def _async_engine(async_db_url: str):
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.db import session as session_module

    engine = create_async_engine(async_db_url, future=True, pool_pre_ping=True)
    session_module._engine = engine
    session_module._session_factory = async_sessionmaker(
        bind=engine, expire_on_commit=False
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture()
async def db(_async_engine):
    from sqlalchemy.ext.asyncio import async_sessionmaker

    factory = async_sessionmaker(bind=_async_engine, expire_on_commit=False)
    async with factory() as s:
        yield s


@pytest_asyncio.fixture()
async def client(_async_engine) -> AsyncIterator["AsyncClient"]:  # noqa: F821
    from httpx import ASGITransport, AsyncClient

    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture()
async def mint(db):
    from sqlalchemy import select

    from app.core.security import mint_token
    from app.models.identity import Role, User, UserRole

    async def _factory(
        *,
        email: str | None = None,
        role_codes: Iterable[str] = (),
        ttl_seconds: int = 3600,
        aud: str | None = None,
        secret: str | None = None,
        jti: str | None = None,
        status: str = "active",
    ) -> TestUser:
        uid = uuid.uuid4()
        addr = email or f"{uid}@example.com"
        db.add(User(id=uid, email=addr, status=status))
        await db.flush()
        for code in role_codes:
            role = (
                await db.execute(select(Role).where(Role.code == code))
            ).scalar_one()
            db.add(UserRole(user_id=uid, role_id=role.id))
        await db.commit()
        token = mint_token(
            sub=uid,
            email=addr,
            ttl_seconds=ttl_seconds,
            aud=aud,
            secret=secret,
            jti=jti or uuid.uuid4().hex,
        )
        return TestUser(id=uid, email=addr, token=token)

    return _factory
