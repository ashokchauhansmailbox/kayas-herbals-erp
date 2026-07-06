"""007 — Distributor + Customer

Creates:
    distributor_tiers, distributors, price_lists, price_list_items,
    kyc_documents,
    customer_profiles, addresses, wallets, wallet_transactions, referrals.

Design notes:
    * A distributor is B2B (business account with a GSTIN + credit limit).
      A customer is B2C (extends `users` via a 1:1 `customer_profiles` row).
    * Tiers control default discount + eligibility for tier-scoped price lists.
    * A price list can be tier-scoped, distributor-scoped, or global.
      `price_list_items` UNIQUE(price_list_id, variant_id).
    * Addresses are per-user; `is_default` is enforced by a partial unique
      index — only one default per (user_id, label).
    * Wallets are 1:1 with users; wallet_transactions are append-only.
    * Referrals connect referrer → referee (referee UNIQUE).

Revision ID: 007
Revises: 006
Create Date: 2026-02-06
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007"
down_revision: Union[str, None] = "006"
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


ACTOR_TABLES = (
    "distributor_tiers",
    "distributors",
    "price_lists",
    "kyc_documents",
    "customer_profiles",
    "addresses",
    "wallets",
    "referrals",
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
    # ---- distributor_tiers ---------------------------------------------
    op.create_table(
        "distributor_tiers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("default_discount_pct", sa.Numeric(5, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        *_actor_soft_delete_cols(),
        sa.UniqueConstraint("code", name="uq_distributor_tiers_code"),
        sa.CheckConstraint("default_discount_pct >= 0 AND default_discount_pct <= 100", name="ck_distributor_tiers_discount_bounds"),
    )
    op.create_index("ix_distributor_tiers_code", "distributor_tiers", ["code"], unique=False)

    # ---- distributors --------------------------------------------------
    op.create_table(
        "distributors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("business_name", sa.String(255), nullable=False),
        sa.Column("legal_name", sa.String(255), nullable=True),
        sa.Column("gstin", sa.String(24), nullable=True),
        sa.Column("pan", sa.String(16), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(24), nullable=True),
        sa.Column("address", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("tier_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("primary_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("credit_limit", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("credit_days", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("current_balance", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("kyc_status", sa.String(24), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("kyc_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("kyc_verified_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        *_actor_soft_delete_cols(),
        sa.ForeignKeyConstraint(["tier_id"], ["distributor_tiers.id"], name="fk_distributors_tier_id_distributor_tiers", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["primary_user_id"], ["users.id"], name="fk_distributors_primary_user_id_users", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["kyc_verified_by"], ["users.id"], name="fk_distributors_kyc_verified_by_users", ondelete="SET NULL"),
        sa.UniqueConstraint("code", name="uq_distributors_code"),
        sa.CheckConstraint("kyc_status IN ('pending','submitted','verified','rejected')", name="ck_distributors_kyc_status"),
        sa.CheckConstraint("credit_limit >= 0 AND credit_days >= 0", name="ck_distributors_credit_nonneg"),
    )
    op.create_index("ix_distributors_code", "distributors", ["code"], unique=False)
    op.create_index("ix_distributors_tier_id", "distributors", ["tier_id"], unique=False)
    op.create_index("ix_distributors_kyc_status", "distributors", ["kyc_status"], unique=False)
    op.create_index("ix_distributors_is_active", "distributors", ["is_active"], unique=False)

    # ---- price_lists ---------------------------------------------------
    op.create_table(
        "price_lists",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("scope", sa.String(24), nullable=False, server_default=sa.text("'global'")),
        sa.Column("tier_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("distributor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("currency", sa.String(8), nullable=False, server_default=sa.text("'INR'")),
        sa.Column("effective_from", sa.Date(), nullable=False, server_default=sa.text("CURRENT_DATE")),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        *_actor_soft_delete_cols(),
        sa.ForeignKeyConstraint(["tier_id"], ["distributor_tiers.id"], name="fk_price_lists_tier_id_distributor_tiers", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["distributor_id"], ["distributors.id"], name="fk_price_lists_distributor_id_distributors", ondelete="CASCADE"),
        sa.UniqueConstraint("code", name="uq_price_lists_code"),
        sa.CheckConstraint("scope IN ('global','tier','distributor')", name="ck_price_lists_scope"),
        sa.CheckConstraint(
            "(scope = 'global' AND tier_id IS NULL AND distributor_id IS NULL) OR "
            "(scope = 'tier' AND tier_id IS NOT NULL AND distributor_id IS NULL) OR "
            "(scope = 'distributor' AND distributor_id IS NOT NULL AND tier_id IS NULL)",
            name="ck_price_lists_scope_consistency",
        ),
    )
    op.create_index("ix_price_lists_scope", "price_lists", ["scope"], unique=False)
    op.create_index("ix_price_lists_tier_id", "price_lists", ["tier_id"], unique=False)
    op.create_index("ix_price_lists_distributor_id", "price_lists", ["distributor_id"], unique=False)
    op.create_index("ix_price_lists_effective_from", "price_lists", ["effective_from"], unique=False)

    # ---- price_list_items ----------------------------------------------
    op.create_table(
        "price_list_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("price_list_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("price", sa.Numeric(14, 2), nullable=False),
        sa.Column("min_qty", sa.Numeric(14, 4), nullable=False, server_default=sa.text("1")),
        sa.Column("max_qty", sa.Numeric(14, 4), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["price_list_id"], ["price_lists.id"], name="fk_price_list_items_price_list_id_price_lists", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"], name="fk_price_list_items_variant_id_product_variants", ondelete="RESTRICT"),
        sa.UniqueConstraint("price_list_id", "variant_id", name="uq_price_list_items_pl_variant"),
        sa.CheckConstraint("price >= 0 AND min_qty > 0", name="ck_price_list_items_price_qty"),
        sa.CheckConstraint("max_qty IS NULL OR max_qty >= min_qty", name="ck_price_list_items_qty_bounds"),
    )
    op.create_index("ix_price_list_items_price_list_id", "price_list_items", ["price_list_id"], unique=False)
    op.create_index("ix_price_list_items_variant_id", "price_list_items", ["variant_id"], unique=False)

    # ---- kyc_documents -------------------------------------------------
    op.create_table(
        "kyc_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("distributor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("doc_type", sa.String(48), nullable=False),
        sa.Column("doc_number", sa.String(96), nullable=True),
        sa.Column("file_url", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.String(96), nullable=True),
        sa.Column("status", sa.String(24), nullable=False, server_default=sa.text("'submitted'")),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        *_actor_soft_delete_cols(),
        sa.ForeignKeyConstraint(["distributor_id"], ["distributors.id"], name="fk_kyc_documents_distributor_id_distributors", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["verified_by"], ["users.id"], name="fk_kyc_documents_verified_by_users", ondelete="SET NULL"),
        sa.CheckConstraint("status IN ('submitted','verified','rejected')", name="ck_kyc_documents_status"),
    )
    op.create_index("ix_kyc_documents_distributor_id", "kyc_documents", ["distributor_id"], unique=False)
    op.create_index("ix_kyc_documents_status", "kyc_documents", ["status"], unique=False)

    # ---- customer_profiles (1:1 with users) ----------------------------
    op.create_table(
        "customer_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("phone", sa.String(24), nullable=True),
        sa.Column("dob", sa.Date(), nullable=True),
        sa.Column("gender", sa.String(16), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("marketing_opt_in", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("preferred_language", sa.String(8), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        *_actor_soft_delete_cols(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_customer_profiles_user_id_users", ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", name="uq_customer_profiles_user_id"),
        sa.CheckConstraint("gender IN ('male','female','other','undisclosed') OR gender IS NULL", name="ck_customer_profiles_gender"),
    )
    op.create_index("ix_customer_profiles_phone", "customer_profiles", ["phone"], unique=False)

    # ---- addresses -----------------------------------------------------
    op.create_table(
        "addresses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("label", sa.String(16), nullable=False, server_default=sa.text("'shipping'")),
        sa.Column("recipient_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(24), nullable=True),
        sa.Column("line1", sa.String(255), nullable=False),
        sa.Column("line2", sa.String(255), nullable=True),
        sa.Column("landmark", sa.String(255), nullable=True),
        sa.Column("city", sa.String(128), nullable=False),
        sa.Column("state", sa.String(128), nullable=False),
        sa.Column("pincode", sa.String(16), nullable=False),
        sa.Column("country", sa.String(64), nullable=False, server_default=sa.text("'IN'")),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        *_actor_soft_delete_cols(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_addresses_user_id_users", ondelete="CASCADE"),
        sa.CheckConstraint("label IN ('billing','shipping','other')", name="ck_addresses_label"),
    )
    op.create_index("ix_addresses_user_id", "addresses", ["user_id"], unique=False)
    # Partial unique: at most one default (user_id, label) among active rows.
    op.execute(
        "CREATE UNIQUE INDEX uq_addresses_default_per_user_label "
        "ON addresses (user_id, label) "
        "WHERE is_default AND is_active AND deleted_at IS NULL;"
    )

    # ---- wallets (1:1 with users) --------------------------------------
    op.create_table(
        "wallets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default=sa.text("'INR'")),
        sa.Column("balance", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        *_actor_soft_delete_cols(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_wallets_user_id_users", ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", name="uq_wallets_user_id"),
        sa.CheckConstraint("balance >= 0", name="ck_wallets_balance_nonneg"),
    )

    # ---- wallet_transactions (append-only) -----------------------------
    op.create_table(
        "wallet_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("wallet_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("balance_after", sa.Numeric(14, 2), nullable=False),
        sa.Column("reference_entity", sa.String(64), nullable=True),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["wallet_id"], ["wallets.id"], name="fk_wallet_transactions_wallet_id_wallets", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], name="fk_wallet_transactions_actor_id_users", ondelete="SET NULL"),
        sa.CheckConstraint("kind IN ('credit','debit')", name="ck_wallet_transactions_kind"),
        sa.CheckConstraint("amount > 0 AND balance_after >= 0", name="ck_wallet_transactions_amount"),
    )
    op.create_index("ix_wallet_transactions_wallet_id_at", "wallet_transactions", ["wallet_id", "at"], unique=False)
    op.create_index("ix_wallet_transactions_ref", "wallet_transactions", ["reference_entity", "reference_id"], unique=False)

    # ---- referrals -----------------------------------------------------
    op.create_table(
        "referrals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("referrer_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("referee_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reward_amount", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(24), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("redeemed_at", sa.DateTime(timezone=True), nullable=True),
        *_actor_soft_delete_cols(),
        sa.ForeignKeyConstraint(["referrer_user_id"], ["users.id"], name="fk_referrals_referrer_user_id_users", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["referee_user_id"], ["users.id"], name="fk_referrals_referee_user_id_users", ondelete="SET NULL"),
        sa.UniqueConstraint("code", name="uq_referrals_code"),
        sa.UniqueConstraint("referee_user_id", name="uq_referrals_referee_user_id"),
        sa.CheckConstraint("status IN ('pending','redeemed','expired','cancelled')", name="ck_referrals_status"),
        sa.CheckConstraint("reward_amount >= 0", name="ck_referrals_reward_nonneg"),
    )
    op.create_index("ix_referrals_referrer_user_id", "referrals", ["referrer_user_id"], unique=False)
    op.create_index("ix_referrals_status", "referrals", ["status"], unique=False)

    # ---- actor FKs -----------------------------------------------------
    for tbl in ACTOR_TABLES:
        _add_actor_fks(tbl)


def downgrade() -> None:
    for tbl in ACTOR_TABLES:
        for col in ("created_by", "updated_by", "deleted_by"):
            op.drop_constraint(f"fk_{tbl}_{col}_users", tbl, type_="foreignkey")

    op.drop_index("ix_referrals_status", table_name="referrals")
    op.drop_index("ix_referrals_referrer_user_id", table_name="referrals")
    op.drop_table("referrals")

    op.drop_index("ix_wallet_transactions_ref", table_name="wallet_transactions")
    op.drop_index("ix_wallet_transactions_wallet_id_at", table_name="wallet_transactions")
    op.drop_table("wallet_transactions")

    op.drop_table("wallets")

    op.execute("DROP INDEX IF EXISTS uq_addresses_default_per_user_label;")
    op.drop_index("ix_addresses_user_id", table_name="addresses")
    op.drop_table("addresses")

    op.drop_index("ix_customer_profiles_phone", table_name="customer_profiles")
    op.drop_table("customer_profiles")

    op.drop_index("ix_kyc_documents_status", table_name="kyc_documents")
    op.drop_index("ix_kyc_documents_distributor_id", table_name="kyc_documents")
    op.drop_table("kyc_documents")

    op.drop_index("ix_price_list_items_variant_id", table_name="price_list_items")
    op.drop_index("ix_price_list_items_price_list_id", table_name="price_list_items")
    op.drop_table("price_list_items")

    op.drop_index("ix_price_lists_effective_from", table_name="price_lists")
    op.drop_index("ix_price_lists_distributor_id", table_name="price_lists")
    op.drop_index("ix_price_lists_tier_id", table_name="price_lists")
    op.drop_index("ix_price_lists_scope", table_name="price_lists")
    op.drop_table("price_lists")

    op.drop_index("ix_distributors_is_active", table_name="distributors")
    op.drop_index("ix_distributors_kyc_status", table_name="distributors")
    op.drop_index("ix_distributors_tier_id", table_name="distributors")
    op.drop_index("ix_distributors_code", table_name="distributors")
    op.drop_table("distributors")

    op.drop_index("ix_distributor_tiers_code", table_name="distributor_tiers")
    op.drop_table("distributor_tiers")
