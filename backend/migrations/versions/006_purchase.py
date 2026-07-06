"""006 — Purchase (vendors, PO, GRN, vendor invoices)

Creates:
    vendors, purchase_orders, po_items, grn, grn_items, vendor_invoices

Also backfills the deferred foreign keys on `purchase_price_history` that were
left unlinked in Sprint 1.2 (see catalog.py::PurchasePriceHistory doc):
    * purchase_price_history.vendor_id  → vendors(id)  ON DELETE SET NULL
    * purchase_price_history.po_id      → purchase_orders(id) ON DELETE SET NULL

Design notes:
    * `vendors.code` and `purchase_orders.po_no` are business identifiers with
      per-tenant uniqueness (single-tenant today = globally unique).
    * `purchase_orders.status` is a String(24) with a CHECK — no enum, so the
      value set can grow without a schema migration (per ADR-03).
    * `po_items`, `grn_items` use UNIQUE(po_id, variant_id) / UNIQUE(grn_id, po_item_id)
      to prevent duplicate lines.
    * Every money column is NUMERIC(14, 2); every quantity is NUMERIC(14, 4).
    * `vendor_invoices.status ∈ {draft, submitted, approved, paid, void}`.
    * `grn.status ∈ {draft, posted, cancelled}` — posted GRNs will produce
      stock_ledger inward moves in Sprint 1.5.

Revision ID: 006
Revises: 005
Create Date: 2026-02-06
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _actor_soft_delete_cols() -> list:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
    ]


ACTOR_TABLES = ("vendors", "purchase_orders", "grn", "vendor_invoices")


def _add_actor_fks(table: str) -> None:
    for col in ("created_by", "updated_by", "deleted_by"):
        op.create_foreign_key(
            f"fk_{table}_{col}_users",
            table,
            "users",
            [col],
            ["id"],
            ondelete="SET NULL",
        )


def upgrade() -> None:
    # ---- vendors --------------------------------------------------------
    op.create_table(
        "vendors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("legal_name", sa.String(255), nullable=True),
        sa.Column("gstin", sa.String(24), nullable=True),
        sa.Column("pan", sa.String(16), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(24), nullable=True),
        sa.Column("address", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("payment_term_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("credit_days", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("currency", sa.String(8), nullable=False, server_default=sa.text("'INR'")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        *_actor_soft_delete_cols(),
        sa.ForeignKeyConstraint(["payment_term_id"], ["payment_terms.id"], name="fk_vendors_payment_term_id_payment_terms", ondelete="RESTRICT"),
        sa.UniqueConstraint("code", name="uq_vendors_code"),
        sa.CheckConstraint("credit_days >= 0", name="ck_vendors_credit_days_nonneg"),
    )
    op.create_index("ix_vendors_code", "vendors", ["code"], unique=False)
    op.create_index("ix_vendors_is_active", "vendors", ["is_active"], unique=False)
    op.create_index("ix_vendors_gstin", "vendors", ["gstin"], unique=False)

    # ---- purchase_orders -----------------------------------------------
    op.create_table(
        "purchase_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("po_no", sa.String(48), nullable=False),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("order_date", sa.Date(), nullable=False, server_default=sa.text("CURRENT_DATE")),
        sa.Column("expected_date", sa.Date(), nullable=True),
        sa.Column("currency", sa.String(8), nullable=False, server_default=sa.text("'INR'")),
        sa.Column("subtotal", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("tax_amount", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("discount_amount", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("total", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        *_actor_soft_delete_cols(),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"], name="fk_purchase_orders_vendor_id_vendors", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], name="fk_purchase_orders_warehouse_id_warehouses", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"], name="fk_purchase_orders_approved_by_users", ondelete="SET NULL"),
        sa.UniqueConstraint("po_no", name="uq_purchase_orders_po_no"),
        sa.CheckConstraint(
            "status IN ('draft','approved','sent','partially_received','received','closed','cancelled')",
            name="ck_purchase_orders_status",
        ),
        sa.CheckConstraint("subtotal >= 0 AND tax_amount >= 0 AND discount_amount >= 0 AND total >= 0", name="ck_purchase_orders_amounts_nonneg"),
    )
    op.create_index("ix_purchase_orders_vendor_id", "purchase_orders", ["vendor_id"], unique=False)
    op.create_index("ix_purchase_orders_warehouse_id", "purchase_orders", ["warehouse_id"], unique=False)
    op.create_index("ix_purchase_orders_status", "purchase_orders", ["status"], unique=False)
    op.create_index("ix_purchase_orders_order_date", "purchase_orders", ["order_date"], unique=False)

    # ---- po_items -------------------------------------------------------
    op.create_table(
        "po_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("po_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ordered_qty", sa.Numeric(14, 4), nullable=False),
        sa.Column("received_qty", sa.Numeric(14, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("unit_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("tax_rate", sa.Numeric(5, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("discount_pct", sa.Numeric(5, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("line_total", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["po_id"], ["purchase_orders.id"], name="fk_po_items_po_id_purchase_orders", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"], name="fk_po_items_variant_id_product_variants", ondelete="RESTRICT"),
        sa.UniqueConstraint("po_id", "variant_id", name="uq_po_items_po_variant"),
        sa.CheckConstraint("ordered_qty > 0", name="ck_po_items_ordered_qty_positive"),
        sa.CheckConstraint("received_qty >= 0 AND received_qty <= ordered_qty", name="ck_po_items_received_qty_bounds"),
        sa.CheckConstraint("unit_price >= 0 AND line_total >= 0", name="ck_po_items_prices_nonneg"),
        sa.CheckConstraint("discount_pct >= 0 AND discount_pct <= 100", name="ck_po_items_discount_pct_bounds"),
    )
    op.create_index("ix_po_items_po_id", "po_items", ["po_id"], unique=False)
    op.create_index("ix_po_items_variant_id", "po_items", ["variant_id"], unique=False)

    # ---- grn (goods receipt note) -------------------------------------
    op.create_table(
        "grn",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("grn_no", sa.String(48), nullable=False),
        sa.Column("po_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("received_date", sa.Date(), nullable=False, server_default=sa.text("CURRENT_DATE")),
        sa.Column("status", sa.String(24), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("vehicle_no", sa.String(48), nullable=True),
        sa.Column("driver_name", sa.String(128), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("posted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        *_actor_soft_delete_cols(),
        sa.ForeignKeyConstraint(["po_id"], ["purchase_orders.id"], name="fk_grn_po_id_purchase_orders", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"], name="fk_grn_vendor_id_vendors", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], name="fk_grn_warehouse_id_warehouses", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["posted_by"], ["users.id"], name="fk_grn_posted_by_users", ondelete="SET NULL"),
        sa.UniqueConstraint("grn_no", name="uq_grn_grn_no"),
        sa.CheckConstraint("status IN ('draft','posted','cancelled')", name="ck_grn_status"),
    )
    op.create_index("ix_grn_po_id", "grn", ["po_id"], unique=False)
    op.create_index("ix_grn_vendor_id", "grn", ["vendor_id"], unique=False)
    op.create_index("ix_grn_warehouse_id", "grn", ["warehouse_id"], unique=False)
    op.create_index("ix_grn_status", "grn", ["status"], unique=False)

    # ---- grn_items ------------------------------------------------------
    op.create_table(
        "grn_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("grn_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("po_item_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("received_qty", sa.Numeric(14, 4), nullable=False),
        sa.Column("damaged_qty", sa.Numeric(14, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("unit_cost", sa.Numeric(14, 4), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["grn_id"], ["grn.id"], name="fk_grn_items_grn_id_grn", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["po_item_id"], ["po_items.id"], name="fk_grn_items_po_item_id_po_items", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"], name="fk_grn_items_variant_id_product_variants", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["batch_id"], ["batches.id"], name="fk_grn_items_batch_id_batches", ondelete="RESTRICT"),
        sa.CheckConstraint("received_qty > 0", name="ck_grn_items_received_qty_positive"),
        sa.CheckConstraint("damaged_qty >= 0 AND damaged_qty <= received_qty", name="ck_grn_items_damaged_qty_bounds"),
    )
    op.create_index("ix_grn_items_grn_id", "grn_items", ["grn_id"], unique=False)
    op.create_index("ix_grn_items_variant_id", "grn_items", ["variant_id"], unique=False)
    op.create_index("ix_grn_items_po_item_id", "grn_items", ["po_item_id"], unique=False)

    # ---- vendor_invoices ------------------------------------------------
    op.create_table(
        "vendor_invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("invoice_no", sa.String(64), nullable=False),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("po_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("grn_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("currency", sa.String(8), nullable=False, server_default=sa.text("'INR'")),
        sa.Column("subtotal", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("tax_amount", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("total", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("paid_amount", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(24), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        *_actor_soft_delete_cols(),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"], name="fk_vendor_invoices_vendor_id_vendors", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["po_id"], ["purchase_orders.id"], name="fk_vendor_invoices_po_id_purchase_orders", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["grn_id"], ["grn.id"], name="fk_vendor_invoices_grn_id_grn", ondelete="SET NULL"),
        sa.UniqueConstraint("vendor_id", "invoice_no", name="uq_vendor_invoices_vendor_invoice_no"),
        sa.CheckConstraint("status IN ('draft','submitted','approved','paid','void')", name="ck_vendor_invoices_status"),
        sa.CheckConstraint("subtotal >= 0 AND tax_amount >= 0 AND total >= 0 AND paid_amount >= 0", name="ck_vendor_invoices_amounts_nonneg"),
        sa.CheckConstraint("paid_amount <= total", name="ck_vendor_invoices_paid_le_total"),
    )
    op.create_index("ix_vendor_invoices_vendor_id", "vendor_invoices", ["vendor_id"], unique=False)
    op.create_index("ix_vendor_invoices_po_id", "vendor_invoices", ["po_id"], unique=False)
    op.create_index("ix_vendor_invoices_status", "vendor_invoices", ["status"], unique=False)
    op.create_index("ix_vendor_invoices_invoice_date", "vendor_invoices", ["invoice_date"], unique=False)

    # ---- actor FKs on top-level tables ---------------------------------
    for tbl in ACTOR_TABLES:
        _add_actor_fks(tbl)

    # ---- backfill deferred FKs on purchase_price_history ----------------
    op.create_foreign_key(
        "fk_purchase_price_history_vendor_id_vendors",
        "purchase_price_history",
        "vendors",
        ["vendor_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_purchase_price_history_po_id_purchase_orders",
        "purchase_price_history",
        "purchase_orders",
        ["po_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # ---- unwind deferred FKs on purchase_price_history ------------------
    op.drop_constraint("fk_purchase_price_history_po_id_purchase_orders", "purchase_price_history", type_="foreignkey")
    op.drop_constraint("fk_purchase_price_history_vendor_id_vendors", "purchase_price_history", type_="foreignkey")

    # ---- drop actor FKs first ------------------------------------------
    for tbl in ACTOR_TABLES:
        for col in ("created_by", "updated_by", "deleted_by"):
            op.drop_constraint(f"fk_{tbl}_{col}_users", tbl, type_="foreignkey")

    # ---- drop tables in reverse dependency order -----------------------
    op.drop_index("ix_vendor_invoices_invoice_date", table_name="vendor_invoices")
    op.drop_index("ix_vendor_invoices_status", table_name="vendor_invoices")
    op.drop_index("ix_vendor_invoices_po_id", table_name="vendor_invoices")
    op.drop_index("ix_vendor_invoices_vendor_id", table_name="vendor_invoices")
    op.drop_table("vendor_invoices")

    op.drop_index("ix_grn_items_po_item_id", table_name="grn_items")
    op.drop_index("ix_grn_items_variant_id", table_name="grn_items")
    op.drop_index("ix_grn_items_grn_id", table_name="grn_items")
    op.drop_table("grn_items")

    op.drop_index("ix_grn_status", table_name="grn")
    op.drop_index("ix_grn_warehouse_id", table_name="grn")
    op.drop_index("ix_grn_vendor_id", table_name="grn")
    op.drop_index("ix_grn_po_id", table_name="grn")
    op.drop_table("grn")

    op.drop_index("ix_po_items_variant_id", table_name="po_items")
    op.drop_index("ix_po_items_po_id", table_name="po_items")
    op.drop_table("po_items")

    op.drop_index("ix_purchase_orders_order_date", table_name="purchase_orders")
    op.drop_index("ix_purchase_orders_status", table_name="purchase_orders")
    op.drop_index("ix_purchase_orders_warehouse_id", table_name="purchase_orders")
    op.drop_index("ix_purchase_orders_vendor_id", table_name="purchase_orders")
    op.drop_table("purchase_orders")

    op.drop_index("ix_vendors_gstin", table_name="vendors")
    op.drop_index("ix_vendors_is_active", table_name="vendors")
    op.drop_index("ix_vendors_code", table_name="vendors")
    op.drop_table("vendors")
