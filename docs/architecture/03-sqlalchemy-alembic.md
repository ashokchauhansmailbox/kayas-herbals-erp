# 03 — SQLAlchemy Models & Alembic Migration Plan

## Layout
```
backend/app/
  db/
    base.py            # Declarative Base + naming convention (for Alembic)
    session.py         # async engine + session factory
    types.py           # PyUUID, TSVector, JSONB helpers
    mixins.py          # TimestampMixin, ActorMixin, SoftDeleteMixin, VersionMixin
  models/
    __init__.py        # explicit imports so Alembic autogenerate sees all
    identity.py        # User, Role, Permission, RolePermission, UserRole, Session, Invitation, AuditLog, ActivityLog
    master_data.py     # Unit, GstRate, HsnCode, Category, Brand, Warehouse, PaymentTerm, TaxRule, Transporter, CourierPartner
    catalog.py         # Product, ProductVariant, ProductImage, Certification, ProductPriceHistory, PurchasePriceHistory
    inventory.py       # Batch, StockLedger, StockSnapshot, StockAdjustment, StockTransfer, StockAlert
    purchase.py        # Vendor, PurchaseOrder, PoItem, Grn, GrnItem, VendorInvoice
    distributor.py     # DistributorTier, DistributorPriceList, Distributor, KycDocument, CustomerLedger
    customer.py        # CustomerProfile, Address, Wallet, Referral
    orders.py          # Order, OrderItem, OrderStatusHistory, Shipment
    billing.py         # Invoice, InvoiceItem, CreditNote, DebitNote, Payment, PaymentReconciliation, Refund
    marketing.py       # Coupon, Campaign, Banner, Newsletter, Review
    support.py         # Ticket, TicketMessage, Return
    settings.py        # BrandSetting, NotificationTemplate, FeatureFlag
```

## Base pattern
```python
# db/base.py
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

NAMING = {
  "ix": "ix_%(table_name)s_%(column_0_label)s",
  "uq": "uq_%(table_name)s_%(column_0_name)s",
  "ck": "ck_%(table_name)s_%(constraint_name)s",
  "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
  "pk": "pk_%(table_name)s",
}
class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING)
```

## Mixins (composed on every business table)
- `TimestampMixin` — `created_at`, `updated_at`
- `ActorMixin` — `created_by`, `updated_by`
- `SoftDeleteMixin` — `deleted_at`, `deleted_by`
- `VersionMixin` — `version` + `mapper_args = {"version_id_col": version}` (optimistic lock)

## Alembic plan
```
migrations/
  env.py                              # async-aware, imports models.*
  versions/
    001_extensions_and_enums.py       # pgcrypto, uuid-ossp, ENUM types
    002_identity_core.py              # users..audit_logs
    003_master_data.py
    004_catalog.py
    005_inventory.py
    006_purchase.py
    007_distributor_and_customer.py
    008_orders.py
    009_billing_and_payments.py
    010_marketing_support_settings.py
    011_indexes_and_views.py          # GIN, partial, v_product_margin
    012_triggers.py                   # version bump, financial hard-delete guard, snapshot recompute
```

## Migration rules
1. Each migration is idempotent; `downgrade()` fully reverses.
2. No `execute("ALTER TABLE …")` string SQL unless wrapped in `op.execute` with a comment explaining why autogenerate can't produce it.
3. Data migrations go in **separate files** prefixed `dm_*.py`.
4. `pre-commit` hook runs `alembic upgrade head && alembic downgrade base && alembic upgrade head` against a throwaway DB.

## Autogenerate discipline
- Every enum → explicit `sa.Enum(name=..., create_type=False)` referencing pre-created type.
- Every JSONB → `postgresql.JSONB(astext_type=Text())`.
- Every UUID → `postgresql.UUID(as_uuid=True)`.

## Seeds (data migration `dm_001_seed_static.py`)
- Permissions catalogue (~120 codes)
- System roles (9 roles) + role→permission mapping
- One `super_admin` user (created via Supabase Admin API; row mirrored here)
- GST rate table (0, 5, 12, 18, 28)
- Units (pcs, g, kg, ml, l, box, strip, bottle)
- Sample HSN codes for herbal categories
- Default warehouse
- Sample brand "Kaya's Herbals"
