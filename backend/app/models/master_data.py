"""Master data models — the reference layer every transactional module depends on.

Tables:
    units, gst_rates, hsn_codes, categories, brands, warehouses,
    payment_terms, tax_rules, transporters, courier_partners

See docs/architecture/08-master-data.md for ownership, seeds, and CRUD scope.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from app.db.base import Base
from app.db.mixins import ActorMixin, SoftDeleteMixin, TimestampMixin, VersionMixin
from app.db.types import PGUUID, jsonb_column, uuid_pk
from sqlalchemy import (
    Boolean,
    Date,
    Enum,
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
# units — units of measure with self-referencing base_unit for conversion
# ---------------------------------------------------------------------------
class Unit(Base, TimestampMixin, ActorMixin, SoftDeleteMixin):
    __tablename__ = "units"

    id = uuid_pk()
    code: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    base_unit_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("units.id", ondelete="SET NULL"),
        nullable=True,
    )
    conversion_factor: Mapped[Decimal] = mapped_column(
        Numeric(18, 6), nullable=False, server_default=text("1")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    __table_args__ = (Index("ix_units_code", "code"),)


# ---------------------------------------------------------------------------
# gst_rates — effective-dated GST slab table
# ---------------------------------------------------------------------------
class GstRate(Base, TimestampMixin, ActorMixin, SoftDeleteMixin):
    __tablename__ = "gst_rates"

    id = uuid_pk()
    rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    __table_args__ = (Index("ix_gst_rates_effective_from", "effective_from"),)


# ---------------------------------------------------------------------------
# hsn_codes
# ---------------------------------------------------------------------------
class HsnCode(Base, TimestampMixin, ActorMixin, SoftDeleteMixin):
    __tablename__ = "hsn_codes"

    id = uuid_pk()
    code: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    default_gst_rate_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("gst_rates.id", ondelete="RESTRICT"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    __table_args__ = (Index("ix_hsn_codes_code", "code"),)


# ---------------------------------------------------------------------------
# categories — self-referencing tree
# ---------------------------------------------------------------------------
class Category(Base, TimestampMixin, ActorMixin, SoftDeleteMixin):
    __tablename__ = "categories"

    id = uuid_pk()
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    parent_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    __table_args__ = (
        Index("ix_categories_slug", "slug"),
        Index("ix_categories_parent_id", "parent_id"),
    )


# ---------------------------------------------------------------------------
# brands
# ---------------------------------------------------------------------------
class Brand(Base, TimestampMixin, ActorMixin, SoftDeleteMixin):
    __tablename__ = "brands"

    id = uuid_pk()
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    logo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manufacturer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    country_of_origin: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    __table_args__ = (Index("ix_brands_slug", "slug"),)


# ---------------------------------------------------------------------------
# warehouses
# ---------------------------------------------------------------------------
class Warehouse(Base, TimestampMixin, ActorMixin, SoftDeleteMixin, VersionMixin):
    __tablename__ = "warehouses"

    id = uuid_pk()
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    gstin: Mapped[Optional[str]] = mapped_column(String(24), nullable=True)
    address = jsonb_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    __table_args__ = (Index("ix_warehouses_code", "code"),)


# ---------------------------------------------------------------------------
# payment_terms
# ---------------------------------------------------------------------------
class PaymentTerm(Base, TimestampMixin, ActorMixin, SoftDeleteMixin):
    __tablename__ = "payment_terms"

    id = uuid_pk()
    code: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(96), nullable=False)
    days: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    __table_args__ = (Index("ix_payment_terms_code", "code"),)


# ---------------------------------------------------------------------------
# tax_rules — composition rules, effective-dated
# ---------------------------------------------------------------------------
class TaxRule(Base, TimestampMixin, ActorMixin, SoftDeleteMixin):
    __tablename__ = "tax_rules"

    id = uuid_pk()
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    mode: Mapped[str] = mapped_column(
        Enum("intra", "inter", "exempt", "zero", name="gst_mode", create_type=False),
        nullable=False,
    )
    components = jsonb_column(nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    __table_args__ = (Index("ix_tax_rules_code", "code"),)


# ---------------------------------------------------------------------------
# transporters
# ---------------------------------------------------------------------------
class Transporter(Base, TimestampMixin, ActorMixin, SoftDeleteMixin):
    __tablename__ = "transporters"

    id = uuid_pk()
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    contact = jsonb_column(nullable=True)
    gstin: Mapped[Optional[str]] = mapped_column(String(24), nullable=True)
    rate_card_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )


# ---------------------------------------------------------------------------
# courier_partners
# ---------------------------------------------------------------------------
class CourierPartner(Base, TimestampMixin, ActorMixin, SoftDeleteMixin):
    __tablename__ = "courier_partners"

    id = uuid_pk()
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    api_config = jsonb_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    __table_args__ = (Index("ix_courier_partners_code", "code"),)


__all__ = [
    "Unit",
    "GstRate",
    "HsnCode",
    "Category",
    "Brand",
    "Warehouse",
    "PaymentTerm",
    "TaxRule",
    "Transporter",
    "CourierPartner",
]
