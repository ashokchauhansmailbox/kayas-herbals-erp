"""Distributor models — tiers, distributor accounts, price lists, KYC.

Sprint 1.4 delivers the schema and master-resource CRUD. Pricing resolution
against orders lands in Sprint 1.5 (Orders + Billing).

Design invariants (see docs/architecture/07-business-rules.md, extended in
docs/database/007-distributor-customer.md):
    BR-DIST-01  Distributor codes are globally unique.
    BR-DIST-02  KYC status ∈ {pending, submitted, verified, rejected}.
    BR-DIST-03  A price list has exactly one scope (global | tier | distributor).
                The CHECK constraint on `price_lists` enforces the tier/distributor
                FK is set for tier/distributor scope and NULL for global.
    BR-DIST-04  Distributor credit_limit and credit_days must be non-negative.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import ActorMixin, SoftDeleteMixin, TimestampMixin, VersionMixin
from app.db.types import PGUUID, jsonb_column, uuid_pk


class DistributorTier(Base, TimestampMixin, ActorMixin, SoftDeleteMixin):
    """Tier a distributor belongs to (e.g. Silver, Gold, Platinum)."""

    __tablename__ = "distributor_tiers"

    id = uuid_pk()
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    default_discount_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, server_default=text("0")
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    __table_args__ = (
        CheckConstraint(
            "default_discount_pct >= 0 AND default_discount_pct <= 100",
            name="ck_distributor_tiers_discount_bounds",
        ),
        Index("ix_distributor_tiers_code", "code"),
    )


class Distributor(Base, TimestampMixin, ActorMixin, SoftDeleteMixin, VersionMixin):
    """A B2B account with credit, KYC, and (optional) tier assignment."""

    __tablename__ = "distributors"

    id = uuid_pk()
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    legal_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    gstin: Mapped[Optional[str]] = mapped_column(String(24), nullable=True)
    pan: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(24), nullable=True)
    address = jsonb_column(nullable=True)
    tier_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("distributor_tiers.id", ondelete="RESTRICT"),
        nullable=True,
    )
    primary_user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    credit_limit: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default=text("0")
    )
    credit_days: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default=text("0")
    )
    kyc_status: Mapped[str] = mapped_column(
        String(24), nullable=False, server_default=text("'pending'")
    )
    kyc_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    kyc_verified_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "kyc_status IN ('pending','submitted','verified','rejected')",
            name="ck_distributors_kyc_status",
        ),
        CheckConstraint(
            "credit_limit >= 0 AND credit_days >= 0",
            name="ck_distributors_credit_nonneg",
        ),
        Index("ix_distributors_code", "code"),
        Index("ix_distributors_tier_id", "tier_id"),
        Index("ix_distributors_kyc_status", "kyc_status"),
        Index("ix_distributors_is_active", "is_active"),
    )


class PriceList(Base, TimestampMixin, ActorMixin, SoftDeleteMixin, VersionMixin):
    """Global / tier / distributor scoped price list."""

    __tablename__ = "price_lists"

    id = uuid_pk()
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    scope: Mapped[str] = mapped_column(
        String(24), nullable=False, server_default=text("'global'")
    )
    tier_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("distributor_tiers.id", ondelete="RESTRICT"),
        nullable=True,
    )
    distributor_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("distributors.id", ondelete="CASCADE"),
        nullable=True,
    )
    currency: Mapped[str] = mapped_column(
        String(8), nullable=False, server_default=text("'INR'")
    )
    effective_from: Mapped[date] = mapped_column(
        Date, nullable=False, server_default=text("CURRENT_DATE")
    )
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "scope IN ('global','tier','distributor')",
            name="ck_price_lists_scope",
        ),
        CheckConstraint(
            "(scope = 'global' AND tier_id IS NULL AND distributor_id IS NULL) OR "
            "(scope = 'tier' AND tier_id IS NOT NULL AND distributor_id IS NULL) OR "
            "(scope = 'distributor' AND distributor_id IS NOT NULL AND tier_id IS NULL)",
            name="ck_price_lists_scope_consistency",
        ),
        Index("ix_price_lists_scope", "scope"),
        Index("ix_price_lists_tier_id", "tier_id"),
        Index("ix_price_lists_distributor_id", "distributor_id"),
        Index("ix_price_lists_effective_from", "effective_from"),
    )


class PriceListItem(Base, TimestampMixin):
    """A line on a price list — one variant, one price, min-qty enforced."""

    __tablename__ = "price_list_items"

    id = uuid_pk()
    price_list_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("price_lists.id", ondelete="CASCADE"),
        nullable=False,
    )
    variant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    min_qty: Mapped[Decimal] = mapped_column(
        Numeric(14, 4), nullable=False, server_default=text("1")
    )
    max_qty: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 4), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "price_list_id", "variant_id", name="uq_price_list_items_pl_variant"
        ),
        CheckConstraint(
            "price >= 0 AND min_qty > 0", name="ck_price_list_items_price_qty"
        ),
        CheckConstraint(
            "max_qty IS NULL OR max_qty >= min_qty",
            name="ck_price_list_items_qty_bounds",
        ),
        Index("ix_price_list_items_price_list_id", "price_list_id"),
        Index("ix_price_list_items_variant_id", "variant_id"),
    )


class KycDocument(Base, TimestampMixin, ActorMixin, SoftDeleteMixin):
    """A KYC document uploaded for a distributor."""

    __tablename__ = "kyc_documents"

    id = uuid_pk()
    distributor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("distributors.id", ondelete="CASCADE"),
        nullable=False,
    )
    doc_type: Mapped[str] = mapped_column(String(48), nullable=False)
    doc_number: Mapped[Optional[str]] = mapped_column(String(96), nullable=True)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(96), nullable=True)
    status: Mapped[str] = mapped_column(
        String(24), nullable=False, server_default=text("'submitted'")
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    verified_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('submitted','verified','rejected')",
            name="ck_kyc_documents_status",
        ),
        Index("ix_kyc_documents_distributor_id", "distributor_id"),
        Index("ix_kyc_documents_status", "status"),
    )


__all__ = [
    "DistributorTier",
    "Distributor",
    "PriceList",
    "PriceListItem",
    "KycDocument",
]
