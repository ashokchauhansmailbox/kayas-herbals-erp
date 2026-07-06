"""003 — Master data

Creates the reference/lookup tables the transactional modules depend on:
    units, gst_rates, hsn_codes, categories, brands, warehouses,
    payment_terms, tax_rules, transporters, courier_partners

All tables carry TimestampMixin + ActorMixin + SoftDeleteMixin (see
`app/db/mixins.py`) so master data changes are audit-friendly and
soft-deletable per BR (docs/architecture/08-master-data.md).

Revision ID: 003
Revises: 002
Create Date: 2026-02-06
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


GST_MODE = postgresql.ENUM(
    "intra", "inter", "exempt", "zero", name="gst_mode", create_type=False
)


def _actor_soft_delete_cols():
    """Standard actor + soft-delete columns (FKs added post-create with use_alter)."""
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
    ]


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


ACTOR_TABLES = (
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
)


def upgrade() -> None:
    # ---- units --------------------------------------------------------
    op.create_table(
        "units",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("code", sa.String(16), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("base_unit_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("conversion_factor", sa.Numeric(18, 6), nullable=False, server_default=sa.text("1")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        *_actor_soft_delete_cols(),
        sa.UniqueConstraint("code", name="uq_units_code"),
    )
    op.create_foreign_key(
        "fk_units_base_unit_id_units",
        "units",
        "units",
        ["base_unit_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_units_code", "units", ["code"], unique=False)

    # ---- gst_rates ----------------------------------------------------
    op.create_table(
        "gst_rates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("rate", sa.Numeric(5, 2), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        *_actor_soft_delete_cols(),
        sa.UniqueConstraint("rate", name="uq_gst_rates_rate"),
    )
    op.create_index("ix_gst_rates_effective_from", "gst_rates", ["effective_from"], unique=False)

    # ---- hsn_codes ----------------------------------------------------
    op.create_table(
        "hsn_codes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("code", sa.String(16), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("default_gst_rate_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        *_actor_soft_delete_cols(),
        sa.ForeignKeyConstraint(
            ["default_gst_rate_id"],
            ["gst_rates.id"],
            name="fk_hsn_codes_default_gst_rate_id_gst_rates",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("code", name="uq_hsn_codes_code"),
    )
    op.create_index("ix_hsn_codes_code", "hsn_codes", ["code"], unique=False)

    # ---- categories ---------------------------------------------------
    op.create_table(
        "categories",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("slug", sa.String(160), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        *_actor_soft_delete_cols(),
        sa.UniqueConstraint("slug", name="uq_categories_slug"),
    )
    op.create_foreign_key(
        "fk_categories_parent_id_categories",
        "categories",
        "categories",
        ["parent_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_categories_slug", "categories", ["slug"], unique=False)
    op.create_index("ix_categories_parent_id", "categories", ["parent_id"], unique=False)

    # ---- brands -------------------------------------------------------
    op.create_table(
        "brands",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("slug", sa.String(160), nullable=False),
        sa.Column("logo_url", sa.Text(), nullable=True),
        sa.Column("manufacturer", sa.String(255), nullable=True),
        sa.Column("country_of_origin", sa.String(64), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        *_actor_soft_delete_cols(),
        sa.UniqueConstraint("name", name="uq_brands_name"),
        sa.UniqueConstraint("slug", name="uq_brands_slug"),
    )
    op.create_index("ix_brands_slug", "brands", ["slug"], unique=False)

    # ---- warehouses ---------------------------------------------------
    op.create_table(
        "warehouses",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("gstin", sa.String(24), nullable=True),
        sa.Column("address", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        *_actor_soft_delete_cols(),
        sa.UniqueConstraint("code", name="uq_warehouses_code"),
    )
    op.create_index("ix_warehouses_code", "warehouses", ["code"], unique=False)

    # ---- payment_terms -----------------------------------------------
    op.create_table(
        "payment_terms",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("code", sa.String(16), nullable=False),
        sa.Column("name", sa.String(96), nullable=False),
        sa.Column("days", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        *_actor_soft_delete_cols(),
        sa.UniqueConstraint("code", name="uq_payment_terms_code"),
    )
    op.create_index("ix_payment_terms_code", "payment_terms", ["code"], unique=False)

    # ---- tax_rules ---------------------------------------------------
    op.create_table(
        "tax_rules",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("mode", GST_MODE, nullable=False),
        sa.Column("components", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        *_actor_soft_delete_cols(),
        sa.UniqueConstraint("code", name="uq_tax_rules_code"),
    )
    op.create_index("ix_tax_rules_code", "tax_rules", ["code"], unique=False)

    # ---- transporters ------------------------------------------------
    op.create_table(
        "transporters",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("contact", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("gstin", sa.String(24), nullable=True),
        sa.Column("rate_card_url", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        *_actor_soft_delete_cols(),
        sa.UniqueConstraint("name", name="uq_transporters_name"),
    )

    # ---- courier_partners --------------------------------------------
    op.create_table(
        "courier_partners",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("api_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        *_actor_soft_delete_cols(),
        sa.UniqueConstraint("code", name="uq_courier_partners_code"),
    )
    op.create_index("ix_courier_partners_code", "courier_partners", ["code"], unique=False)

    # ---- actor FKs (added after all tables to avoid ordering issues) --
    for tbl in ACTOR_TABLES:
        _add_actor_fks(tbl)


def downgrade() -> None:
    # Drop actor FKs first (reverse order irrelevant, all target `users`).
    for tbl in ACTOR_TABLES:
        for col in ("created_by", "updated_by", "deleted_by"):
            op.drop_constraint(f"fk_{tbl}_{col}_users", tbl, type_="foreignkey")

    op.drop_index("ix_courier_partners_code", table_name="courier_partners")
    op.drop_table("courier_partners")

    op.drop_table("transporters")

    op.drop_index("ix_tax_rules_code", table_name="tax_rules")
    op.drop_table("tax_rules")

    op.drop_index("ix_payment_terms_code", table_name="payment_terms")
    op.drop_table("payment_terms")

    op.drop_index("ix_warehouses_code", table_name="warehouses")
    op.drop_table("warehouses")

    op.drop_index("ix_brands_slug", table_name="brands")
    op.drop_table("brands")

    op.drop_index("ix_categories_parent_id", table_name="categories")
    op.drop_index("ix_categories_slug", table_name="categories")
    op.drop_constraint("fk_categories_parent_id_categories", "categories", type_="foreignkey")
    op.drop_table("categories")

    op.drop_index("ix_hsn_codes_code", table_name="hsn_codes")
    op.drop_table("hsn_codes")

    op.drop_index("ix_gst_rates_effective_from", table_name="gst_rates")
    op.drop_table("gst_rates")

    op.drop_index("ix_units_code", table_name="units")
    op.drop_constraint("fk_units_base_unit_id_units", "units", type_="foreignkey")
    op.drop_table("units")
