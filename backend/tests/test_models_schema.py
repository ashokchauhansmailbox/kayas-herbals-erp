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

# Sprint 1.1 tables.
IDENTITY_TABLES = {
    "users",
    "roles",
    "permissions",
    "role_permissions",
    "user_roles",
    "sessions",
    "user_invitations",
    "audit_logs",
    "activity_logs",
}
MASTER_DATA_TABLES = {
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

# Sprint 1.2 tables.
CATALOG_TABLES = {
    "products",
    "product_variants",
    "product_images",
    "product_documents",
    "certifications",
    "product_price_history",
    "purchase_price_history",
}
INVENTORY_TABLES = {
    "batches",
    "stock_adjustments",
    "stock_transfers",
    "stock_transfer_items",
    "stock_ledger",
    "stock_snapshots",
    "stock_alerts",
}

EXPECTED_TABLES = (
    IDENTITY_TABLES | MASTER_DATA_TABLES | CATALOG_TABLES | INVENTORY_TABLES
)

# Tables that must carry timestamp columns.
TIMESTAMPED = EXPECTED_TABLES - {
    "role_permissions",
    "user_roles",
    "audit_logs",
    "activity_logs",
    "product_price_history",
    "purchase_price_history",
    "stock_ledger",
}

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
    "products",
    "product_variants",
    "product_images",
    "product_documents",
    "certifications",
    "batches",
    "stock_adjustments",
    "stock_transfers",
}


def test_all_expected_tables_registered():
    registered = set(Base.metadata.tables.keys())
    missing = EXPECTED_TABLES - registered
    assert not missing, f"Missing tables: {missing}"


def test_no_unexpected_tables():
    """Sprints 1.1 + 1.2 define exactly EXPECTED_TABLES."""
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
    for name in EXPECTED_TABLES:
        if name in {"users", "role_permissions", "user_roles"}:
            continue
        tbl = Base.metadata.tables[name]
        id_col = tbl.c["id"]
        assert id_col.primary_key, f"{name}.id must be PK"
        assert id_col.server_default is not None, f"{name}.id needs server_default"
        assert "gen_random_uuid" in str(
            id_col.server_default.arg
        ), f"{name}.id server_default is {id_col.server_default.arg!r}"


def test_audit_log_is_wide():
    tbl = Base.metadata.tables["audit_logs"]
    for col in ("actor_id", "entity", "action", "before", "after", "diff", "at"):
        assert col in tbl.c, f"audit_logs missing {col}"


def test_activity_log_shape():
    tbl = Base.metadata.tables["activity_logs"]
    for col in ("actor_id", "event", "payload", "at"):
        assert col in tbl.c, f"activity_logs missing {col}"


def test_master_data_actor_columns():
    for name in {
        "units",
        "gst_rates",
        "hsn_codes",
        "categories",
        "brands",
        "warehouses",
    }:
        tbl = Base.metadata.tables[name]
        assert "created_by" in tbl.c
        assert "updated_by" in tbl.c


def test_catalog_models_reexported():
    for name in (
        "Product",
        "ProductVariant",
        "ProductImage",
        "ProductDocument",
        "Certification",
        "ProductPriceHistory",
        "PurchasePriceHistory",
    ):
        assert hasattr(models, name), f"app.models must re-export {name}"


def test_inventory_models_reexported():
    for name in (
        "Batch",
        "StockAdjustment",
        "StockTransfer",
        "StockTransferItem",
        "StockLedger",
        "StockSnapshot",
        "StockAlert",
    ):
        assert hasattr(models, name), f"app.models must re-export {name}"


def test_product_unique_constraints():
    products = Base.metadata.tables["products"]
    unique_cols = {
        tuple(sorted(c.name for c in con.columns))
        for con in products.constraints
        if con.__class__.__name__ == "UniqueConstraint"
    }
    assert ("sku",) in unique_cols, "products.sku must be UNIQUE"
    assert ("slug",) in unique_cols, "products.slug must be UNIQUE"


def test_variant_barcode_unique():
    variants = Base.metadata.tables["product_variants"]
    unique_cols = {
        tuple(sorted(c.name for c in con.columns))
        for con in variants.constraints
        if con.__class__.__name__ == "UniqueConstraint"
    }
    assert ("sku",) in unique_cols, "product_variants.sku must be UNIQUE"
    assert ("barcode",) in unique_cols, "product_variants.barcode must be UNIQUE"


def test_stock_transfer_check_constraints():
    tbl = Base.metadata.tables["stock_transfers"]
    ck_names = {
        c.name for c in tbl.constraints if c.__class__.__name__ == "CheckConstraint"
    }
    assert "ck_stock_transfers_different_warehouses" in ck_names


def test_stock_ledger_qty_nonzero_check():
    tbl = Base.metadata.tables["stock_ledger"]
    ck_names = {
        c.name for c in tbl.constraints if c.__class__.__name__ == "CheckConstraint"
    }
    assert "ck_stock_ledger_qty_nonzero" in ck_names


def test_stock_snapshot_available_nonnegative_check():
    tbl = Base.metadata.tables["stock_snapshots"]
    ck_names = {
        c.name for c in tbl.constraints if c.__class__.__name__ == "CheckConstraint"
    }
    assert "ck_stock_snapshots_available_nonnegative" in ck_names


def test_batches_variant_batch_no_unique():
    tbl = Base.metadata.tables["batches"]
    unique_pairs = {
        tuple(sorted(c.name for c in con.columns))
        for con in tbl.constraints
        if con.__class__.__name__ == "UniqueConstraint"
    }
    assert ("batch_no", "variant_id") in unique_pairs


def test_price_history_journals_have_no_soft_delete():
    """Journals are strictly append-only — no update/delete semantics."""
    for name in ("product_price_history", "purchase_price_history", "stock_ledger"):
        tbl = Base.metadata.tables[name]
        assert "deleted_at" not in tbl.c, f"{name} must not carry deleted_at"
        assert "updated_at" not in tbl.c, f"{name} must not carry updated_at"


def test_purchase_price_history_vendor_and_po_columns_present_without_fk():
    """Sprint 1.3 will add the FKs when vendors + purchase_orders exist."""
    tbl = Base.metadata.tables["purchase_price_history"]
    assert "vendor_id" in tbl.c
    assert "po_id" in tbl.c
    fk_targets = {fk.column.table.name for fk in tbl.foreign_keys}
    assert "vendors" not in fk_targets
    assert "purchase_orders" not in fk_targets
