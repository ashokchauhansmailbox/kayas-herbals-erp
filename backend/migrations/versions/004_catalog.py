"""004 — Catalog

Creates the product catalog tables:
    products, product_variants, product_images, product_documents,
    certifications, product_price_history, purchase_price_history.

Dependencies:
    * migration 001 — extensions + enums
    * migration 003 — master_data (categories / brands / hsn_codes / units)

`purchase_price_history.vendor_id` and `.po_id` are UUID columns without
FK constraints yet — Sprint 1.3 (Purchase) will add the FKs once
`vendors` / `purchase_orders` tables exist.

Revision ID: 004
Revises: 003
Create Date: 2026-02-06
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _actor_soft_delete_cols():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
    ]


ACTOR_TABLES = (
    "products",
    "product_variants",
    "product_images",
    "product_documents",
    "certifications",
)


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
    # ---- products ----------------------------------------------------
    op.create_table(
        "products",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("sku", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("hsn_code_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("default_unit_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("fssai_licence", sa.String(64), nullable=True),
        sa.Column("ayush_licence", sa.String(64), nullable=True),
        sa.Column("manufacturer", sa.String(255), nullable=True),
        sa.Column("country_of_origin", sa.String(64), nullable=True),
        sa.Column("shelf_life_days", sa.Integer(), nullable=True),
        sa.Column("storage_instructions", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("benefits", sa.Text(), nullable=True),
        sa.Column("ingredients", sa.Text(), nullable=True),
        sa.Column("dosage", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        *_actor_soft_delete_cols(),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], name="fk_products_category_id_categories", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], name="fk_products_brand_id_brands", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["hsn_code_id"], ["hsn_codes.id"], name="fk_products_hsn_code_id_hsn_codes", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["default_unit_id"], ["units.id"], name="fk_products_default_unit_id_units", ondelete="RESTRICT"),
        sa.UniqueConstraint("sku", name="uq_products_sku"),
        sa.UniqueConstraint("slug", name="uq_products_slug"),
    )
    op.create_index("ix_products_sku", "products", ["sku"], unique=False)
    op.create_index("ix_products_slug", "products", ["slug"], unique=False)
    op.create_index("ix_products_category_id", "products", ["category_id"], unique=False)
    op.create_index("ix_products_brand_id", "products", ["brand_id"], unique=False)
    op.create_index("ix_products_is_active", "products", ["is_active"], unique=False)

    # ---- product_variants -------------------------------------------
    op.create_table(
        "product_variants",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sku", sa.String(64), nullable=False),
        sa.Column("variant_name", sa.String(255), nullable=False),
        sa.Column("mrp", sa.Numeric(14, 2), nullable=False),
        sa.Column("base_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("pack_size", sa.Numeric(14, 4), nullable=True),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("barcode", sa.String(64), nullable=True),
        sa.Column("qr_code_url", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        *_actor_soft_delete_cols(),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name="fk_product_variants_product_id_products", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"], name="fk_product_variants_unit_id_units", ondelete="RESTRICT"),
        sa.UniqueConstraint("sku", name="uq_product_variants_sku"),
        sa.UniqueConstraint("barcode", name="uq_product_variants_barcode"),
    )
    op.create_index("ix_product_variants_product_id", "product_variants", ["product_id"], unique=False)
    op.create_index("ix_product_variants_sku", "product_variants", ["sku"], unique=False)
    op.create_index("ix_product_variants_barcode", "product_variants", ["barcode"], unique=False)

    # ---- product_images ---------------------------------------------
    op.create_table(
        "product_images",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("alt", sa.String(255), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        *_actor_soft_delete_cols(),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"], name="fk_product_images_variant_id_product_variants", ondelete="CASCADE"),
    )
    op.create_index("ix_product_images_variant_id", "product_images", ["variant_id", "sort_order"], unique=False)

    # ---- product_documents ------------------------------------------
    op.create_table(
        "product_documents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("doc_type", sa.String(48), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("file_url", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.String(96), nullable=True),
        sa.Column("version_label", sa.String(32), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        *_actor_soft_delete_cols(),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name="fk_product_documents_product_id_products", ondelete="CASCADE"),
    )
    op.create_index("ix_product_documents_product_id", "product_documents", ["product_id"], unique=False)
    op.create_index("ix_product_documents_doc_type", "product_documents", ["doc_type"], unique=False)

    # ---- certifications ---------------------------------------------
    op.create_table(
        "certifications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(48), nullable=False),
        sa.Column("number", sa.String(96), nullable=False),
        sa.Column("issued_by", sa.String(255), nullable=True),
        sa.Column("issued_on", sa.Date(), nullable=True),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("file_url", sa.Text(), nullable=True),
        *_actor_soft_delete_cols(),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name="fk_certifications_product_id_products", ondelete="CASCADE"),
    )
    op.create_index("ix_certifications_product_id", "certifications", ["product_id"], unique=False)
    op.create_index("ix_certifications_type", "certifications", ["type"], unique=False)
    op.create_index("ix_certifications_valid_until", "certifications", ["valid_until"], unique=False)

    # ---- product_price_history (append-only journal) ----------------
    op.create_table(
        "product_price_history",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("price", sa.Numeric(14, 2), nullable=False),
        sa.Column("mrp", sa.Numeric(14, 2), nullable=True),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"], name="fk_product_price_history_variant_id_product_variants", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"], name="fk_product_price_history_changed_by_users", ondelete="SET NULL"),
    )
    op.create_index("ix_product_price_history_variant_id", "product_price_history", ["variant_id", "effective_from"], unique=False)

    # ---- purchase_price_history (append-only journal) ---------------
    op.create_table(
        "purchase_price_history",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=False),
        # vendor_id / po_id kept nullable + FK-less; Sprint 1.3 adds FKs to
        # vendors / purchase_orders once those tables exist.
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("po_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("price", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default=sa.text("'INR'")),
        sa.Column("quantity", sa.Numeric(14, 4), nullable=True),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("recorded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"], name="fk_purchase_price_history_variant_id_product_variants", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recorded_by"], ["users.id"], name="fk_purchase_price_history_recorded_by_users", ondelete="SET NULL"),
    )
    op.create_index("ix_purchase_price_history_variant_id", "purchase_price_history", ["variant_id", "at"], unique=False)
    op.create_index("ix_purchase_price_history_vendor_id", "purchase_price_history", ["vendor_id"], unique=False)

    # ---- actor FKs (post-create to avoid ordering with users) --------
    for tbl in ACTOR_TABLES:
        _add_actor_fks(tbl)


def downgrade() -> None:
    for tbl in ACTOR_TABLES:
        for col in ("created_by", "updated_by", "deleted_by"):
            op.drop_constraint(f"fk_{tbl}_{col}_users", tbl, type_="foreignkey")

    op.drop_index("ix_purchase_price_history_vendor_id", table_name="purchase_price_history")
    op.drop_index("ix_purchase_price_history_variant_id", table_name="purchase_price_history")
    op.drop_table("purchase_price_history")

    op.drop_index("ix_product_price_history_variant_id", table_name="product_price_history")
    op.drop_table("product_price_history")

    op.drop_index("ix_certifications_valid_until", table_name="certifications")
    op.drop_index("ix_certifications_type", table_name="certifications")
    op.drop_index("ix_certifications_product_id", table_name="certifications")
    op.drop_table("certifications")

    op.drop_index("ix_product_documents_doc_type", table_name="product_documents")
    op.drop_index("ix_product_documents_product_id", table_name="product_documents")
    op.drop_table("product_documents")

    op.drop_index("ix_product_images_variant_id", table_name="product_images")
    op.drop_table("product_images")

    op.drop_index("ix_product_variants_barcode", table_name="product_variants")
    op.drop_index("ix_product_variants_sku", table_name="product_variants")
    op.drop_index("ix_product_variants_product_id", table_name="product_variants")
    op.drop_table("product_variants")

    op.drop_index("ix_products_is_active", table_name="products")
    op.drop_index("ix_products_brand_id", table_name="products")
    op.drop_index("ix_products_category_id", table_name="products")
    op.drop_index("ix_products_slug", table_name="products")
    op.drop_index("ix_products_sku", table_name="products")
    op.drop_table("products")
