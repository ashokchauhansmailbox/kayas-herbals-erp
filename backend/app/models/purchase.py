"""Purchase models — vendors, purchase orders, GRNs, vendor invoices.

Sprint 1.4 delivers the schema and master-resource CRUD (vendors). The
transactional lifecycle (PO approval → GRN posting → invoice reconciliation)
ships in Sprint 1.5 alongside Orders + Billing.

Design invariants (docs/architecture/07-business-rules.md, extended in
docs/database/006-purchase.md):
    BR-PUR-01  Vendor codes are globally unique.
    BR-PUR-02  PO totals must be non-negative and consistent with line items
               (subtotal + tax + freight - discount == total). The
               consistency check is enforced at the service layer, not the
               CHECK constraint (line-item aggregation is dynamic).
    BR-PUR-03  A PO transitions draft → approved → sent →
               (partially_received | received) → closed | cancelled.
    BR-PUR-04  GRN quantities cannot exceed the outstanding PO qty when the
               GRN is linked to a PO (received_qty <= ordered_qty - already_received).
    BR-PUR-05  vendor_invoices.paid_amount <= total (DB CHECK).
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


class Vendor(Base, TimestampMixin, ActorMixin, SoftDeleteMixin, VersionMixin):
    """A supplier from whom the business procures product variants."""

    __tablename__ = "vendors"

    id = uuid_pk()
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    legal_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    gstin: Mapped[Optional[str]] = mapped_column(String(24), nullable=True)
    pan: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(24), nullable=True)
    address = jsonb_column(nullable=True)
    payment_term_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("payment_terms.id", ondelete="RESTRICT"),
        nullable=True,
    )
    credit_days: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    currency: Mapped[str] = mapped_column(
        String(8), nullable=False, server_default=text("'INR'")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("credit_days >= 0", name="ck_vendors_credit_days_nonneg"),
        Index("ix_vendors_code", "code"),
        Index("ix_vendors_is_active", "is_active"),
        Index("ix_vendors_gstin", "gstin"),
    )


class PurchaseOrder(Base, TimestampMixin, ActorMixin, SoftDeleteMixin, VersionMixin):
    """A purchase order raised against a vendor for a target warehouse."""

    __tablename__ = "purchase_orders"

    id = uuid_pk()
    po_no: Mapped[str] = mapped_column(String(48), nullable=False, unique=True)
    vendor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("vendors.id", ondelete="RESTRICT"),
        nullable=False,
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(24), nullable=False, server_default=text("'draft'")
    )
    order_date: Mapped[date] = mapped_column(
        Date, nullable=False, server_default=text("CURRENT_DATE")
    )
    expected_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(
        String(8), nullable=False, server_default=text("'INR'")
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default=text("0")
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default=text("0")
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default=text("0")
    )
    total: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default=text("0")
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    approved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','approved','sent','partially_received','received','closed','cancelled')",
            name="ck_purchase_orders_status",
        ),
        CheckConstraint(
            "subtotal >= 0 AND tax_amount >= 0 AND discount_amount >= 0 AND total >= 0",
            name="ck_purchase_orders_amounts_nonneg",
        ),
        Index("ix_purchase_orders_vendor_id", "vendor_id"),
        Index("ix_purchase_orders_warehouse_id", "warehouse_id"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_order_date", "order_date"),
    )


class PurchaseOrderItem(Base, TimestampMixin):
    """A line on a purchase order — one variant, one price, one tax rate."""

    __tablename__ = "po_items"

    id = uuid_pk()
    po_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    variant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    ordered_qty: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    received_qty: Mapped[Decimal] = mapped_column(
        Numeric(14, 4), nullable=False, server_default=text("0")
    )
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, server_default=text("0")
    )
    discount_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, server_default=text("0")
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default=text("0")
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("po_id", "variant_id", name="uq_po_items_po_variant"),
        CheckConstraint("ordered_qty > 0", name="ck_po_items_ordered_qty_positive"),
        CheckConstraint(
            "received_qty >= 0 AND received_qty <= ordered_qty",
            name="ck_po_items_received_qty_bounds",
        ),
        CheckConstraint(
            "unit_price >= 0 AND line_total >= 0",
            name="ck_po_items_prices_nonneg",
        ),
        CheckConstraint(
            "discount_pct >= 0 AND discount_pct <= 100",
            name="ck_po_items_discount_pct_bounds",
        ),
        Index("ix_po_items_po_id", "po_id"),
        Index("ix_po_items_variant_id", "variant_id"),
    )


class GRN(Base, TimestampMixin, ActorMixin, SoftDeleteMixin, VersionMixin):
    """Goods Receipt Note — records physical receipt against (optionally) a PO."""

    __tablename__ = "grn"

    id = uuid_pk()
    grn_no: Mapped[str] = mapped_column(String(48), nullable=False, unique=True)
    po_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="RESTRICT"),
        nullable=True,
    )
    vendor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("vendors.id", ondelete="RESTRICT"),
        nullable=False,
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
    )
    received_date: Mapped[date] = mapped_column(
        Date, nullable=False, server_default=text("CURRENT_DATE")
    )
    status: Mapped[str] = mapped_column(
        String(24), nullable=False, server_default=text("'draft'")
    )
    vehicle_no: Mapped[Optional[str]] = mapped_column(String(48), nullable=True)
    driver_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    posted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    posted_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','posted','cancelled')",
            name="ck_grn_status",
        ),
        Index("ix_grn_po_id", "po_id"),
        Index("ix_grn_vendor_id", "vendor_id"),
        Index("ix_grn_warehouse_id", "warehouse_id"),
        Index("ix_grn_status", "status"),
    )


class GRNItem(Base, TimestampMixin):
    """A line on a GRN — one variant, optionally linked to a PO item + batch."""

    __tablename__ = "grn_items"

    id = uuid_pk()
    grn_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("grn.id", ondelete="CASCADE"),
        nullable=False,
    )
    po_item_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("po_items.id", ondelete="SET NULL"),
        nullable=True,
    )
    variant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    batch_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("batches.id", ondelete="RESTRICT"),
        nullable=True,
    )
    received_qty: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    damaged_qty: Mapped[Decimal] = mapped_column(
        Numeric(14, 4), nullable=False, server_default=text("0")
    )
    unit_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 4), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "received_qty > 0", name="ck_grn_items_received_qty_positive"
        ),
        CheckConstraint(
            "damaged_qty >= 0 AND damaged_qty <= received_qty",
            name="ck_grn_items_damaged_qty_bounds",
        ),
        Index("ix_grn_items_grn_id", "grn_id"),
        Index("ix_grn_items_variant_id", "variant_id"),
        Index("ix_grn_items_po_item_id", "po_item_id"),
    )


class VendorInvoice(Base, TimestampMixin, ActorMixin, SoftDeleteMixin, VersionMixin):
    """Vendor-issued invoice, optionally 3-way-matched against a PO + GRN."""

    __tablename__ = "vendor_invoices"

    id = uuid_pk()
    invoice_no: Mapped[str] = mapped_column(String(64), nullable=False)
    vendor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("vendors.id", ondelete="RESTRICT"),
        nullable=False,
    )
    po_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    grn_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("grn.id", ondelete="SET NULL"),
        nullable=True,
    )
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(
        String(8), nullable=False, server_default=text("'INR'")
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default=text("0")
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default=text("0")
    )
    total: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default=text("0")
    )
    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default=text("0")
    )
    status: Mapped[str] = mapped_column(
        String(24), nullable=False, server_default=text("'draft'")
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "vendor_id", "invoice_no", name="uq_vendor_invoices_vendor_invoice_no"
        ),
        CheckConstraint(
            "status IN ('draft','submitted','approved','paid','void')",
            name="ck_vendor_invoices_status",
        ),
        CheckConstraint(
            "subtotal >= 0 AND tax_amount >= 0 AND total >= 0 AND paid_amount >= 0",
            name="ck_vendor_invoices_amounts_nonneg",
        ),
        CheckConstraint(
            "paid_amount <= total", name="ck_vendor_invoices_paid_le_total"
        ),
        Index("ix_vendor_invoices_vendor_id", "vendor_id"),
        Index("ix_vendor_invoices_po_id", "po_id"),
        Index("ix_vendor_invoices_status", "status"),
        Index("ix_vendor_invoices_invoice_date", "invoice_date"),
    )


__all__ = [
    "Vendor",
    "PurchaseOrder",
    "PurchaseOrderItem",
    "GRN",
    "GRNItem",
    "VendorInvoice",
]
