"""Inventory models.

Tables:
    batches              — lot-level identity (mfg date, expiry, cost/unit)
    stock_ledger         — append-only stock movement journal
    stock_snapshots      — materialised balance per (variant, warehouse, batch, state)
    stock_adjustments    — header for manual adjustments (line items → ledger)
    stock_transfers      — header for inter-warehouse transfers
    stock_transfer_items — line items on a transfer
    stock_alerts         — materialised low-stock + near-expiry alerts

Design invariants (docs/architecture/07-business-rules.md):
    BR-INV-01  Stock tracked per (variant, warehouse, batch, state).
    BR-INV-02  Every movement transfers qty between states or warehouses.
    BR-INV-06  Damaged units go to `damaged` state with a mandatory reason.
    BR-INV-08  Negative available stock forbidden — CHECK on snapshot qty.

The stock_valuation view is created in migration 005 (not represented here).
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
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column


# ---------------------------------------------------------------------------
# batches — lot-level identity
# ---------------------------------------------------------------------------
class Batch(Base, TimestampMixin, ActorMixin, SoftDeleteMixin, VersionMixin):
    __tablename__ = "batches"

    id = uuid_pk()
    variant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    batch_no: Mapped[str] = mapped_column(String(64), nullable=False)
    mfg_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    qty_manufactured: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    cost_per_unit: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(14, 4), nullable=True
    )
    supplier_ref: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("variant_id", "batch_no", name="uq_batches_variant_id"),
        Index("ix_batches_variant_id", "variant_id"),
        Index("ix_batches_expiry_date", "expiry_date"),
    )


# ---------------------------------------------------------------------------
# stock_adjustments — header for manual stock adjustments
# ---------------------------------------------------------------------------
class StockAdjustment(Base, TimestampMixin, ActorMixin, SoftDeleteMixin, VersionMixin):
    __tablename__ = "stock_adjustments"

    id = uuid_pk()
    reference_no: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    warehouse_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
    )
    reason_code: Mapped[str] = mapped_column(String(32), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(24), nullable=False, server_default=text("'draft'")
    )
    posted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    posted_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_stock_adjustments_warehouse_id", "warehouse_id"),
        Index("ix_stock_adjustments_status", "status"),
    )


# ---------------------------------------------------------------------------
# stock_transfers — header for inter-warehouse transfers
# ---------------------------------------------------------------------------
class StockTransfer(Base, TimestampMixin, ActorMixin, SoftDeleteMixin, VersionMixin):
    __tablename__ = "stock_transfers"

    id = uuid_pk()
    reference_no: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    from_warehouse_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
    )
    to_warehouse_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(24), nullable=False, server_default=text("'draft'")
    )
    dispatched_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    received_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "from_warehouse_id <> to_warehouse_id",
            name="different_warehouses",
        ),
        Index("ix_stock_transfers_from_warehouse_id", "from_warehouse_id"),
        Index("ix_stock_transfers_to_warehouse_id", "to_warehouse_id"),
        Index("ix_stock_transfers_status", "status"),
    )


# ---------------------------------------------------------------------------
# stock_transfer_items — line items on a transfer
# ---------------------------------------------------------------------------
class StockTransferItem(Base, TimestampMixin):
    __tablename__ = "stock_transfer_items"

    id = uuid_pk()
    transfer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("stock_transfers.id", ondelete="CASCADE"),
        nullable=False,
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
    qty: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)

    __table_args__ = (
        CheckConstraint("qty > 0", name="qty_positive"),
        Index("ix_stock_transfer_items_transfer_id", "transfer_id"),
    )


# ---------------------------------------------------------------------------
# stock_ledger — append-only movement journal
# ---------------------------------------------------------------------------
class StockLedger(Base):
    __tablename__ = "stock_ledger"

    id = uuid_pk()
    variant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
    )
    batch_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("batches.id", ondelete="RESTRICT"),
        nullable=True,
    )
    move_type: Mapped[str] = mapped_column(
        Enum(
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
        ),
        nullable=False,
    )
    qty: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    state_from: Mapped[Optional[str]] = mapped_column(
        Enum(
            "available",
            "reserved",
            "damaged",
            "returned",
            "expired",
            name="stock_state",
            create_type=False,
        ),
        nullable=True,
    )
    state_to: Mapped[str] = mapped_column(
        Enum(
            "available",
            "reserved",
            "damaged",
            "returned",
            "expired",
            name="stock_state",
            create_type=False,
        ),
        nullable=False,
    )
    ref_entity: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ref_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    actor_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        CheckConstraint("qty <> 0", name="qty_nonzero"),
        Index("ix_stock_ledger_variant_wh_at", "variant_id", "warehouse_id", "at"),
        Index("ix_stock_ledger_batch_id", "batch_id"),
        Index("ix_stock_ledger_ref", "ref_entity", "ref_id"),
        Index("ix_stock_ledger_move_type", "move_type", "at"),
    )


# ---------------------------------------------------------------------------
# stock_snapshots — materialised balance
# UNIQUE(variant_id, warehouse_id, batch_id, state)
# ---------------------------------------------------------------------------
class StockSnapshot(Base, TimestampMixin):
    __tablename__ = "stock_snapshots"

    id = uuid_pk()
    variant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
    )
    batch_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("batches.id", ondelete="RESTRICT"),
        nullable=True,
    )
    state: Mapped[str] = mapped_column(
        Enum(
            "available",
            "reserved",
            "damaged",
            "returned",
            "expired",
            name="stock_state",
            create_type=False,
        ),
        nullable=False,
    )
    qty: Mapped[Decimal] = mapped_column(
        Numeric(14, 4), nullable=False, server_default=text("0")
    )
    last_movement_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("stock_ledger.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        # NULLs are distinct in Postgres — batch_id can be NULL for aggregate
        # snapshots. The functional unique index below coalesces NULL batches
        # to the zero UUID so we still get one row per natural key.
        Index(
            "uq_stock_snapshots_natural_key",
            "variant_id",
            "warehouse_id",
            text("COALESCE(batch_id, '00000000-0000-0000-0000-000000000000'::uuid)"),
            "state",
            unique=True,
        ),
        Index("ix_stock_snapshots_state", "state"),
        Index("ix_stock_snapshots_variant_wh", "variant_id", "warehouse_id"),
        CheckConstraint(
            "state = 'available' AND qty >= 0 OR state <> 'available'",
            name="available_nonnegative",
        ),
    )


# ---------------------------------------------------------------------------
# stock_alerts — low-stock + near-expiry alerts
# ---------------------------------------------------------------------------
class StockAlert(Base, TimestampMixin):
    __tablename__ = "stock_alerts"

    id = uuid_pk()
    alert_type: Mapped[str] = mapped_column(String(32), nullable=False)
    severity: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'warning'")
    )
    variant_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="CASCADE"),
        nullable=True,
    )
    warehouse_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="CASCADE"),
        nullable=True,
    )
    batch_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("batches.id", ondelete="CASCADE"),
        nullable=True,
    )
    threshold_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(14, 4), nullable=True
    )
    current_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(14, 4), nullable=True
    )
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raised_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_stock_alerts_alert_type", "alert_type", "raised_at"),
        Index("ix_stock_alerts_variant_id", "variant_id"),
        Index("ix_stock_alerts_warehouse_id", "warehouse_id"),
        Index("ix_stock_alerts_open", "resolved_at"),
    )


__all__ = [
    "Batch",
    "StockAdjustment",
    "StockTransfer",
    "StockTransferItem",
    "StockLedger",
    "StockSnapshot",
    "StockAlert",
]
