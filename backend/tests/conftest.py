"""Shared pytest fixtures for Sprint 1.1 + 1.2 tests.

Uses per-worker test databases so pytest-xdist workers don't collide when
tests mutate schema/state.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")


def _base_sync_url() -> str | None:
    url = os.environ.get("DATABASE_URL_TEST_SYNC") or os.environ.get("DATABASE_URL_SYNC")
    if not url:
        return None
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
    return url


def _admin_url_and_dbname(sync_url: str) -> tuple[str, str]:
    """Return (admin_connection_url, current_db_name)."""
    # Strip the trailing /dbname to get an admin url pointing at postgres.
    prefix, _, dbname = sync_url.rpartition("/")
    admin = f"{prefix}/postgres"
    return admin, dbname


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
    # `worker_id` is "master" when running serially, else "gw0", "gw1", ...
    admin_url, base_db = _admin_url_and_dbname(base)
    suffix = "" if worker_id == "master" else f"_{worker_id}"
    dbname = f"{base_db}{suffix}"
    _ensure_db(admin_url, dbname)
    return f"{admin_url.rsplit('/', 1)[0]}/{dbname}"


@pytest.fixture(scope="session")
def alembic_ini() -> str:
    return str(BACKEND_DIR / "alembic.ini")


@pytest.fixture(autouse=True, scope="session")
def _apply_migrations_once(sync_db_url: str) -> None:
    """Applied once per worker; ensures schema exists before any tests run."""
    subprocess.run(
        ["alembic", "-x", f"db_url={sync_db_url}", "upgrade", "head"],
        cwd=BACKEND_DIR,
        check=True,
        capture_output=True,
    )
