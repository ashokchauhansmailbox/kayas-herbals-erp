"""Product Catalog models.

Tables:
    products
    product_variants
    product_images
    product_documents
    certifications
    product_price_history      (selling-price journal — variant scope)
    purchase_price_history     (buy-price journal — variant scope)

Design notes (from docs/architecture/02-database-schema.md):
    * SKUs are unique at both product and variant level (variant SKU is the
      shipped identifier; the product-level SKU is the "family" id).
    * Slugs uniquely identify a product in storefront URLs.
    * `mrp`, `base_price`, and every price journal column use NUMERIC(14,2).
    * `product_price_history` and `purchase_price_history` are strictly
      append-only journals — no updates.
    * Ayurveda/Ayush + FSSAI attributes live on `products` (not variants).
    * `purchase_price_history.vendor_id` and `.po_id` are UUID columns
      without FK constraints yet — Sprint 1.3 (purchase) will add the
      FKs once `vendors` / `purchase_orders` tables exist.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from app.db.base import Base
from app.db.mixins import ActorMixin, SoftDeleteMixin, TimestampMixin, VersionMixin
from app.db.types import PGUUID, uuid_pk
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column


# ---------------------------------------------------------------------------
# products — SKU master, family-level metadata
# ---------------------------------------------------------------------------
class Product(Base, TimestampMixin, ActorMixin, SoftDeleteMixin, VersionMixin):
    __tablename__ = "products"

    id = uuid_pk()
    sku: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    category_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=True,
    )
    brand_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="RESTRICT"),
        nullable=True,
    )
    hsn_code_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hsn_codes.id", ondelete="RESTRICT"),
        nullable=True,
    )
    default_unit_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("units.id", ondelete="RESTRICT"),
        nullable=True,
    )

    fssai_licence: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ayush_licence: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    manufacturer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    country_of_origin: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    shelf_life_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    storage_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    benefits: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ingredients: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dosage: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    __table_args__ = (
        Index("ix_products_sku", "sku"),
        Index("ix_products_slug", "slug"),
        Index("ix_products_category_id", "category_id"),
        Index("ix_products_brand_id", "brand_id"),
        Index("ix_products_is_active", "is_active"),
    )


# ---------------------------------------------------------------------------
# product_variants — size / potency SKUs, the shipped units
# ---------------------------------------------------------------------------
class ProductVariant(Base, TimestampMixin, ActorMixin, SoftDeleteMixin, VersionMixin):
    __tablename__ = "product_variants"

    id = uuid_pk()
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    sku: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    variant_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mrp: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    base_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    pack_size: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 4), nullable=True)
    unit_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("units.id", ondelete="RESTRICT"),
        nullable=True,
    )
    barcode: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, unique=True
    )
    qr_code_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    __table_args__ = (
        Index("ix_product_variants_product_id", "product_id"),
        Index("ix_product_variants_sku", "sku"),
        Index("ix_product_variants_barcode", "barcode"),
    )


# ---------------------------------------------------------------------------
# product_images — variant-scoped media
# ---------------------------------------------------------------------------
class ProductImage(Base, TimestampMixin, ActorMixin, SoftDeleteMixin):
    __tablename__ = "product_images"

    id = uuid_pk()
    variant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="CASCADE"),
        nullable=False,
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    alt: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )

    __table_args__ = (
        Index("ix_product_images_variant_id", "variant_id", "sort_order"),
    )


# ---------------------------------------------------------------------------
# product_documents — spec sheets, brochures, MSDS, lab reports, etc.
# ---------------------------------------------------------------------------
class ProductDocument(Base, TimestampMixin, ActorMixin, SoftDeleteMixin):
    __tablename__ = "product_documents"

    id = uuid_pk()
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    doc_type: Mapped[str] = mapped_column(String(48), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(96), nullable=True)
    version_label: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    is_public: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )

    __table_args__ = (
        Index("ix_product_documents_product_id", "product_id"),
        Index("ix_product_documents_doc_type", "doc_type"),
    )


# ---------------------------------------------------------------------------
# certifications — AYUSH / FSSAI / organic / lab
# ---------------------------------------------------------------------------
class Certification(Base, TimestampMixin, ActorMixin, SoftDeleteMixin):
    __tablename__ = "certifications"

    id = uuid_pk()
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(String(48), nullable=False)
    number: Mapped[str] = mapped_column(String(96), nullable=False)
    issued_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    issued_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    valid_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    file_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_certifications_product_id", "product_id"),
        Index("ix_certifications_type", "type"),
        Index("ix_certifications_valid_until", "valid_until"),
    )


# ---------------------------------------------------------------------------
# product_price_history — selling-price journal (append-only)
# ---------------------------------------------------------------------------
class ProductPriceHistory(Base):
    __tablename__ = "product_price_history"

    id = uuid_pk()
    variant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="CASCADE"),
        nullable=False,
    )
    price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    mrp: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    effective_to: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    changed_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    __table_args__ = (
        Index("ix_product_price_history_variant_id", "variant_id", "effective_from"),
    )


# ---------------------------------------------------------------------------
# purchase_price_history — buy-price journal (append-only)
# vendor_id / po_id are UUID columns without FK yet; Sprint 1.3 adds the FKs.
# ---------------------------------------------------------------------------
class PurchasePriceHistory(Base):
    __tablename__ = "purchase_price_history"

    id = uuid_pk()
    variant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="CASCADE"),
        nullable=False,
    )
    vendor_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    po_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(8), nullable=False, server_default=text("'INR'")
    )
    quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 4), nullable=True)
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    recorded_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_purchase_price_history_variant_id", "variant_id", "at"),
        Index("ix_purchase_price_history_vendor_id", "vendor_id"),
    )


__all__ = [
    "Product",
    "ProductVariant",
    "ProductImage",
    "ProductDocument",
    "Certification",
    "ProductPriceHistory",
    "PurchasePriceHistory",
]
