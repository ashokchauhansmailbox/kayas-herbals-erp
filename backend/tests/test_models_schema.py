"""Model contract tests — no DB required.

Verifies that every mapped class:
    * is registered on `Base.metadata`
    * has the expected mixin columns
    * uses PostgreSQL-appropriate types where relevant
"""
from __future__ import annotations

import pytest

from app import models
from app.db.base import Base

EXPECTED_TABLES = {
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
    # master_data
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
}

# Tables that must carry timestamp columns (either directly or via mixin).
TIMESTAMPED = EXPECTED_TABLES - {"role_permissions", "user_roles", "audit_logs", "activity_logs"}

# Tables that must have soft-delete columns.
SOFT_DELETED = {
    "users",
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
}


def test_all_expected_tables_registered():
    registered = set(Base.metadata.tables.keys())
    missing = EXPECTED_TABLES - registered
    assert not missing, f"Missing tables: {missing}"


def test_no_unexpected_tables():
    """Sprint 1.1 defines exactly EXPECTED_TABLES. Alerts on stray tables."""
    registered = set(Base.metadata.tables.keys())
    unexpected = registered - EXPECTED_TABLES
    assert not unexpected, f"Unexpected tables (belong in later sprints): {unexpected}"


@pytest.mark.parametrize("table_name", sorted(TIMESTAMPED))
def test_timestamp_columns(table_name: str):
    tbl = Base.metadata.tables[table_name]
    assert "created_at" in tbl.c, f"{table_name} missing created_at"
    assert "updated_at" in tbl.c, f"{table_name} missing updated_at"


@pytest.mark.parametrize("table_name", sorted(SOFT_DELETED))
def test_soft_delete_columns(table_name: str):
    tbl = Base.metadata.tables[table_name]
    assert "deleted_at" in tbl.c, f"{table_name} missing deleted_at"
    assert "deleted_by" in tbl.c, f"{table_name} missing deleted_by"


def test_users_pk_is_uuid_no_server_default():
    """users.id is Supabase-supplied — must NOT auto-generate on insert."""
    users = Base.metadata.tables["users"]
    id_col = users.c["id"]
    assert id_col.primary_key
    assert id_col.server_default is None, "users.id must not have a server_default"


def test_uuid_pks_have_gen_random_uuid_default():
    """All other UUID PKs default to gen_random_uuid()."""
    for name in EXPECTED_TABLES:
        if name in {"users", "role_permissions", "user_roles"}:
            continue  # composite PK or Supabase-owned
        tbl = Base.metadata.tables[name]
        id_col = tbl.c["id"]
        assert id_col.primary_key, f"{name}.id must be PK"
        assert id_col.server_default is not None, f"{name}.id needs server_default"
        assert "gen_random_uuid" in str(id_col.server_default.arg), (
            f"{name}.id server_default is {id_col.server_default.arg!r}"
        )


def test_audit_log_is_wide():
    tbl = Base.metadata.tables["audit_logs"]
    for col in ("actor_id", "entity", "action", "before", "after", "diff", "at"):
        assert col in tbl.c, f"audit_logs missing {col}"


def test_activity_log_shape():
    tbl = Base.metadata.tables["activity_logs"]
    for col in ("actor_id", "event", "payload", "at"):
        assert col in tbl.c, f"activity_logs missing {col}"


def test_master_data_actor_columns():
    for name in {"units", "gst_rates", "hsn_codes", "categories", "brands", "warehouses"}:
        tbl = Base.metadata.tables[name]
        assert "created_by" in tbl.c
        assert "updated_by" in tbl.c


def test_models_module_reexports():
    """`from app.models import User` must work — Alembic autogenerate relies on it."""
    for name in (
        "User",
        "Role",
        "Permission",
        "Unit",
        "GstRate",
        "HsnCode",
        "Category",
        "Brand",
        "Warehouse",
    ):
        assert hasattr(models, name), f"app.models must re-export {name}"
