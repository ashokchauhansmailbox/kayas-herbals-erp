"""005 — Inventory + stock valuation view

Creates:
    batches, stock_adjustments, stock_transfers, stock_transfer_items,
    stock_ledger, stock_snapshots, stock_alerts

Plus the read-only view:
    v_stock_valuation — per (variant, warehouse, batch, state) balance
                        joined with the batch cost-per-unit to compute
                        `total_value` and expose expiry data.

Dependencies:
    * migration 001 — stock_move_type / stock_state enums
    * migration 003 — warehouses
    * migration 004 — product_variants (required as FK for batches, ledger, etc.)

Revision ID: 005
Revises: 004
Create Date: 2026-02-06
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


STOCK_MOVE_TYPE = postgresql.ENUM(
    "inward",
    "outward",
    "transfer_in",
    "transfer_out",
    "adjust_plus",
    "adjust_minus",
    "damage",
    "return",
    "expire",
    "reserve",
    "release",
    name="stock_move_type",
    create_type=False,
)

STOCK_STATE = postgresql.ENUM(
    "available", "reserved", "damaged", "returned", "expired",
    name="stock_state", create_type=False,
)


def _actor_soft_delete_cols():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
    ]


ACTOR_TABLES = ("batches", "stock_adjustments", "stock_transfers")


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


STOCK_VALUATION_VIEW_UP = """
CREATE OR REPLACE VIEW v_stock_valuation AS
SELECT
    s.variant_id,
    s.warehouse_id,
    s.batch_id,
    s.state,
    s.qty,
    b.cost_per_unit,
    (s.qty * COALESCE(b.cost_per_unit, 0))::NUMERIC(20, 4) AS total_value,
    b.batch_no,
    b.mfg_date,
    b.expiry_date,
    CASE
        WHEN b.expiry_date IS NULL THEN NULL
        ELSE (b.expiry_date - CURRENT_DATE)
    END AS days_to_expiry
FROM stock_snapshots s
LEFT JOIN batches b ON b.id = s.batch_id
WHERE s.qty <> 0;
"""

STOCK_VALUATION_VIEW_DOWN = "DROP VIEW IF EXISTS v_stock_valuation;"


def upgrade() -> None:
    # ---- batches -----------------------------------------------------
    op.create_table(
        "batches",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batch_no", sa.String(64), nullable=False),
        sa.Column("mfg_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("qty_manufactured", sa.Numeric(14, 4), nullable=False),
        sa.Column("cost_per_unit", sa.Numeric(14, 4), nullable=True),
        sa.Column("supplier_ref", sa.String(128), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        *_actor_soft_delete_cols(),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"], name="fk_batches_variant_id_product_variants", ondelete="RESTRICT"),
        sa.UniqueConstraint("variant_id", "batch_no", name="uq_batches_variant_id"),
    )
    op.create_index("ix_batches_variant_id", "batches", ["variant_id"], unique=False)
    op.create_index("ix_batches_expiry_date", "batches", ["expiry_date"], unique=False)

    # ---- stock_adjustments -------------------------------------------
    op.create_table(
        "stock_adjustments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("reference_no", sa.String(64), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason_code", sa.String(32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(24), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("posted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        *_actor_soft_delete_cols(),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], name="fk_stock_adjustments_warehouse_id_warehouses", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["posted_by"], ["users.id"], name="fk_stock_adjustments_posted_by_users", ondelete="SET NULL"),
        sa.UniqueConstraint("reference_no", name="uq_stock_adjustments_reference_no"),
    )
    op.create_index("ix_stock_adjustments_warehouse_id", "stock_adjustments", ["warehouse_id"], unique=False)
    op.create_index("ix_stock_adjustments_status", "stock_adjustments", ["status"], unique=False)

    # ---- stock_transfers --------------------------------------------
    op.create_table(
        "stock_transfers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("reference_no", sa.String(64), nullable=False),
        sa.Column("from_warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("to_warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        *_actor_soft_delete_cols(),
        sa.ForeignKeyConstraint(["from_warehouse_id"], ["warehouses.id"], name="fk_stock_transfers_from_warehouse_id_warehouses", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["to_warehouse_id"], ["warehouses.id"], name="fk_stock_transfers_to_warehouse_id_warehouses", ondelete="RESTRICT"),
        sa.CheckConstraint(
            "from_warehouse_id <> to_warehouse_id",
            name="ck_stock_transfers_different_warehouses",
        ),
        sa.UniqueConstraint("reference_no", name="uq_stock_transfers_reference_no"),
    )
    op.create_index("ix_stock_transfers_from_warehouse_id", "stock_transfers", ["from_warehouse_id"], unique=False)
    op.create_index("ix_stock_transfers_to_warehouse_id", "stock_transfers", ["to_warehouse_id"], unique=False)
    op.create_index("ix_stock_transfers_status", "stock_transfers", ["status"], unique=False)

    # ---- stock_transfer_items ---------------------------------------
    op.create_table(
        "stock_transfer_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("transfer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("qty", sa.Numeric(14, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["transfer_id"], ["stock_transfers.id"], name="fk_stock_transfer_items_transfer_id_stock_transfers", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"], name="fk_stock_transfer_items_variant_id_product_variants", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["batch_id"], ["batches.id"], name="fk_stock_transfer_items_batch_id_batches", ondelete="RESTRICT"),
        sa.CheckConstraint("qty > 0", name="ck_stock_transfer_items_qty_positive"),
    )
    op.create_index("ix_stock_transfer_items_transfer_id", "stock_transfer_items", ["transfer_id"], unique=False)

    # ---- stock_ledger (append-only) ---------------------------------
    op.create_table(
        "stock_ledger",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("move_type", STOCK_MOVE_TYPE, nullable=False),
        sa.Column("qty", sa.Numeric(14, 4), nullable=False),
        sa.Column("state_from", STOCK_STATE, nullable=True),
        sa.Column("state_to", STOCK_STATE, nullable=False),
        sa.Column("ref_entity", sa.String(64), nullable=True),
        sa.Column("ref_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"], name="fk_stock_ledger_variant_id_product_variants", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], name="fk_stock_ledger_warehouse_id_warehouses", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["batch_id"], ["batches.id"], name="fk_stock_ledger_batch_id_batches", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], name="fk_stock_ledger_actor_id_users", ondelete="SET NULL"),
        sa.CheckConstraint("qty <> 0", name="ck_stock_ledger_qty_nonzero"),
    )
    op.create_index("ix_stock_ledger_variant_wh_at", "stock_ledger", ["variant_id", "warehouse_id", "at"], unique=False)
    op.create_index("ix_stock_ledger_batch_id", "stock_ledger", ["batch_id"], unique=False)
    op.create_index("ix_stock_ledger_ref", "stock_ledger", ["ref_entity", "ref_id"], unique=False)
    op.create_index("ix_stock_ledger_move_type", "stock_ledger", ["move_type", "at"], unique=False)

    # ---- stock_snapshots --------------------------------------------
    op.create_table(
        "stock_snapshots",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("state", STOCK_STATE, nullable=False),
        sa.Column("qty", sa.Numeric(14, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("last_movement_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"], name="fk_stock_snapshots_variant_id_product_variants", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], name="fk_stock_snapshots_warehouse_id_warehouses", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["batch_id"], ["batches.id"], name="fk_stock_snapshots_batch_id_batches", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["last_movement_id"], ["stock_ledger.id"], name="fk_stock_snapshots_last_movement_id_stock_ledger", ondelete="SET NULL"),
        sa.CheckConstraint(
            "state = 'available' AND qty >= 0 OR state <> 'available'",
            name="ck_stock_snapshots_available_nonnegative",
        ),
    )
    op.create_index("ix_stock_snapshots_state", "stock_snapshots", ["state"], unique=False)
    op.create_index("ix_stock_snapshots_variant_wh", "stock_snapshots", ["variant_id", "warehouse_id"], unique=False)
    # Partial-unique index on the natural key using COALESCE to make NULL batch_id distinct.
    op.execute(
        """
        CREATE UNIQUE INDEX uq_stock_snapshots_natural_key
        ON stock_snapshots (variant_id, warehouse_id, COALESCE(batch_id, '00000000-0000-0000-0000-000000000000'::uuid), state);
        """
    )

    # ---- stock_alerts -----------------------------------------------
    op.create_table(
        "stock_alerts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("alert_type", sa.String(32), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False, server_default=sa.text("'warning'")),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("threshold_value", sa.Numeric(14, 4), nullable=True),
        sa.Column("current_value", sa.Numeric(14, 4), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("raised_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"], name="fk_stock_alerts_variant_id_product_variants", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], name="fk_stock_alerts_warehouse_id_warehouses", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["batch_id"], ["batches.id"], name="fk_stock_alerts_batch_id_batches", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resolved_by"], ["users.id"], name="fk_stock_alerts_resolved_by_users", ondelete="SET NULL"),
    )
    op.create_index("ix_stock_alerts_alert_type", "stock_alerts", ["alert_type", "raised_at"], unique=False)
    op.create_index("ix_stock_alerts_variant_id", "stock_alerts", ["variant_id"], unique=False)
    op.create_index("ix_stock_alerts_warehouse_id", "stock_alerts", ["warehouse_id"], unique=False)
    op.create_index("ix_stock_alerts_open", "stock_alerts", ["resolved_at"], unique=False)

    # ---- actor FKs ---------------------------------------------------
    for tbl in ACTOR_TABLES:
        _add_actor_fks(tbl)

    # ---- v_stock_valuation view -------------------------------------
    op.execute(STOCK_VALUATION_VIEW_UP)


def downgrade() -> None:
    op.execute(STOCK_VALUATION_VIEW_DOWN)

    for tbl in ACTOR_TABLES:
        for col in ("created_by", "updated_by", "deleted_by"):
            op.drop_constraint(f"fk_{tbl}_{col}_users", tbl, type_="foreignkey")

    op.drop_index("ix_stock_alerts_open", table_name="stock_alerts")
    op.drop_index("ix_stock_alerts_warehouse_id", table_name="stock_alerts")
    op.drop_index("ix_stock_alerts_variant_id", table_name="stock_alerts")
    op.drop_index("ix_stock_alerts_alert_type", table_name="stock_alerts")
    op.drop_table("stock_alerts")

    op.execute("DROP INDEX IF EXISTS uq_stock_snapshots_natural_key;")
    op.drop_index("ix_stock_snapshots_variant_wh", table_name="stock_snapshots")
    op.drop_index("ix_stock_snapshots_state", table_name="stock_snapshots")
    op.drop_table("stock_snapshots")

    op.drop_index("ix_stock_ledger_move_type", table_name="stock_ledger")
    op.drop_index("ix_stock_ledger_ref", table_name="stock_ledger")
    op.drop_index("ix_stock_ledger_batch_id", table_name="stock_ledger")
    op.drop_index("ix_stock_ledger_variant_wh_at", table_name="stock_ledger")
    op.drop_table("stock_ledger")

    op.drop_index("ix_stock_transfer_items_transfer_id", table_name="stock_transfer_items")
    op.drop_table("stock_transfer_items")

    op.drop_index("ix_stock_transfers_status", table_name="stock_transfers")
    op.drop_index("ix_stock_transfers_to_warehouse_id", table_name="stock_transfers")
    op.drop_index("ix_stock_transfers_from_warehouse_id", table_name="stock_transfers")
    op.drop_table("stock_transfers")

    op.drop_index("ix_stock_adjustments_status", table_name="stock_adjustments")
    op.drop_index("ix_stock_adjustments_warehouse_id", table_name="stock_adjustments")
    op.drop_table("stock_adjustments")

    op.drop_index("ix_batches_expiry_date", table_name="batches")
    op.drop_index("ix_batches_variant_id", table_name="batches")
    op.drop_table("batches")
