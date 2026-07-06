"""Shared pytest fixtures for Sprint 1.1 tests."""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")


def _sync_url() -> str | None:
    url = os.environ.get("DATABASE_URL_TEST_SYNC") or os.environ.get("DATABASE_URL_SYNC")
    if not url:
        return None
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
    return url


@pytest.fixture(scope="session")
def sync_db_url() -> str:
    url = _sync_url()
    if not url:
        pytest.skip("DATABASE_URL_TEST_SYNC / DATABASE_URL_SYNC not configured")
    return url


@pytest.fixture(scope="session")
def alembic_ini() -> str:
    return str(BACKEND_DIR / "alembic.ini")
