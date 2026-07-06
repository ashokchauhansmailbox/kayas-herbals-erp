"""Integration test: `alembic upgrade head → downgrade base → upgrade head`.

Requires a live Postgres reachable via DATABASE_URL_TEST_SYNC.
Runs against `kaya_bos_test` so it never mutates the dev DB.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _run_alembic(url: str, *args: str) -> None:
    subprocess.run(
        ["alembic", "-x", f"db_url={url}", *args],
        cwd=BACKEND_DIR,
        check=True,
        capture_output=True,
    )


@pytest.fixture(scope="module")
def clean_test_db(sync_db_url: str) -> str:
    """Downgrade to base before each test module so state is deterministic.

    Re-runs the idempotent seed at teardown so downstream tests scheduled to
    the same xdist worker see the same baseline (permissions, roles, etc.)
    that the session-scoped autouse fixture provided.
    """
    import os

    _run_alembic(sync_db_url, "downgrade", "base")
    yield sync_db_url
    _run_alembic(sync_db_url, "upgrade", "head")
    # Re-seed so subsequent test modules on this worker see a populated DB.
    async_url = sync_db_url.replace(
        "postgresql+psycopg2://", "postgresql+asyncpg://", 1
    )
    result = subprocess.run(
        ["python", "-m", "app.seeds.run"],
        cwd=BACKEND_DIR,
        env={**os.environ, "DATABASE_URL": async_url},
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:  # pragma: no cover — surfaces at teardown
        raise RuntimeError(
            f"Re-seed after migration cycle failed:\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


def test_upgrade_head_creates_expected_tables(clean_test_db: str):
    _run_alembic(clean_test_db, "upgrade", "head")
    engine = create_engine(clean_test_db)
    with engine.connect() as conn:
        rows = (
            conn.execute(
                text(
                    "SELECT tablename FROM pg_tables "
                    "WHERE schemaname = 'public' ORDER BY tablename"
                )
            )
            .scalars()
            .all()
        )
    engine.dispose()
    assert "alembic_version" in rows
    for expected in (
        # identity
        "users",
        "roles",
        "permissions",
        "role_permissions",
        "user_roles",
        "sessions",
        "user_invitations",
        "audit_logs",
        "activity_logs",
        # master data
        "units",
        "gst_rates",
        "hsn_codes",
        "categories",
        "brands",
        "warehouses",
        "payment_terms",
        "tax_rules",
        "transporters",
        "courier_partners",
        # catalog
        "products",
        "product_variants",
        "product_images",
        "product_documents",
        "certifications",
        "product_price_history",
        "purchase_price_history",
        # inventory
        "batches",
        "stock_adjustments",
        "stock_transfers",
        "stock_transfer_items",
        "stock_ledger",
        "stock_snapshots",
        "stock_alerts",
    ):
        assert expected in rows, f"missing table: {expected}"


def test_stock_valuation_view_exists(clean_test_db: str):
    _run_alembic(clean_test_db, "upgrade", "head")
    engine = create_engine(clean_test_db)
    with engine.connect() as conn:
        views = (
            conn.execute(
                text("SELECT viewname FROM pg_views WHERE schemaname = 'public'")
            )
            .scalars()
            .all()
        )
    engine.dispose()
    assert "v_stock_valuation" in views


def test_downgrade_base_removes_all_tables(clean_test_db: str):
    _run_alembic(clean_test_db, "upgrade", "head")
    _run_alembic(clean_test_db, "downgrade", "base")
    engine = create_engine(clean_test_db)
    with engine.connect() as conn:
        rows = (
            conn.execute(
                text(
                    "SELECT tablename FROM pg_tables "
                    "WHERE schemaname = 'public' AND tablename != 'alembic_version'"
                )
            )
            .scalars()
            .all()
        )
    engine.dispose()
    assert rows == [], f"leftover tables after downgrade base: {rows}"


def test_enums_installed_after_upgrade(clean_test_db: str):
    _run_alembic(clean_test_db, "upgrade", "head")
    engine = create_engine(clean_test_db)
    with engine.connect() as conn:
        types = (
            conn.execute(
                text("SELECT typname FROM pg_type WHERE typtype = 'e' ORDER BY typname")
            )
            .scalars()
            .all()
        )
    engine.dispose()
    for enum in (
        "user_status",
        "stock_state",
        "stock_move_type",
        "order_status",
        "order_source",
        "payment_status",
        "invoice_status",
        "gst_mode",
        "kyc_status",
    ):
        assert enum in types, f"missing enum: {enum}"


def test_extensions_installed(clean_test_db: str):
    _run_alembic(clean_test_db, "upgrade", "head")
    engine = create_engine(clean_test_db)
    with engine.connect() as conn:
        exts = (
            conn.execute(text("SELECT extname FROM pg_extension ORDER BY extname"))
            .scalars()
            .all()
        )
    engine.dispose()
    for ext in ("pgcrypto", "pg_trgm", "citext"):
        assert ext in exts, f"missing extension: {ext}"


def test_no_autogenerate_drift(clean_test_db: str):
    """`alembic check` must return zero pending ops after upgrade head."""
    _run_alembic(clean_test_db, "upgrade", "head")
    result = subprocess.run(
        ["alembic", "-x", f"db_url={clean_test_db}", "check"],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
    )
    combined = (result.stdout + result.stderr).lower()
    assert "no new upgrade operations" in combined, combined
