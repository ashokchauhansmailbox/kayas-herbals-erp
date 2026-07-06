"""Customer models — customer profile, addresses, wallet, referrals.

Sprint 1.4 delivers the schema and `/me` self-service routes for authenticated
customers. Business rules that debit the wallet (order placement, refunds)
land in Sprint 1.5.

Design invariants:
    BR-CUST-01  A customer profile is a 1:1 extension of a user (UNIQUE user_id).
    BR-CUST-02  Only one default address per (user, label) — enforced by a
                partial unique index in migration 007.
    BR-CUST-03  Wallet balance is non-negative (DB CHECK). A debit that would
                take balance below zero must be refused at the service layer.
    BR-CUST-04  wallet_transactions is append-only — no updates or deletes.
    BR-CUST-05  A referee can be linked to at most one referrer (UNIQUE
                referee_user_id).
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
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import ActorMixin, SoftDeleteMixin, TimestampMixin, VersionMixin
from app.db.types import PGUUID, uuid_pk


class CustomerProfile(Base, TimestampMixin, ActorMixin, SoftDeleteMixin, VersionMixin):
    """Optional profile row extending `users` for B2C customers."""

    __tablename__ = "customer_profiles"

    id = uuid_pk()
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    phone: Mapped[Optional[str]] = mapped_column(String(24), nullable=True)
    dob: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    marketing_opt_in: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    preferred_language: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "gender IN ('male','female','other','undisclosed') OR gender IS NULL",
            name="ck_customer_profiles_gender",
        ),
        Index("ix_customer_profiles_phone", "phone"),
    )


class Address(Base, TimestampMixin, ActorMixin, SoftDeleteMixin):
    """A postal address owned by a user (billing / shipping / other)."""

    __tablename__ = "addresses"

    id = uuid_pk()
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    label: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'shipping'")
    )
    recipient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(24), nullable=True)
    line1: Mapped[str] = mapped_column(String(255), nullable=False)
    line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    landmark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(128), nullable=False)
    state: Mapped[str] = mapped_column(String(128), nullable=False)
    pincode: Mapped[str] = mapped_column(String(16), nullable=False)
    country: Mapped[str] = mapped_column(
        String(64), nullable=False, server_default=text("'IN'")
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    __table_args__ = (
        CheckConstraint(
            "label IN ('billing','shipping','other')", name="ck_addresses_label"
        ),
        Index("ix_addresses_user_id", "user_id"),
        # One default (user_id, label) among active, non-deleted rows.
        # Kept in the model so `alembic check` sees the same object it built
        # via `op.execute(CREATE UNIQUE INDEX ...)` in migration 007.
        Index(
            "uq_addresses_default_per_user_label",
            "user_id",
            "label",
            unique=True,
            postgresql_where=text("is_default AND is_active AND deleted_at IS NULL"),
        ),
    )


class Wallet(Base, TimestampMixin, ActorMixin, SoftDeleteMixin, VersionMixin):
    """A user's wallet — 1:1 with users, currency-scoped, balance-guarded."""

    __tablename__ = "wallets"

    id = uuid_pk()
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    currency: Mapped[str] = mapped_column(
        String(8), nullable=False, server_default=text("'INR'")
    )
    balance: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default=text("0")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    __table_args__ = (
        CheckConstraint("balance >= 0", name="ck_wallets_balance_nonneg"),
    )


class WalletTransaction(Base):
    """Append-only wallet ledger — every balance change lands here."""

    __tablename__ = "wallet_transactions"

    id = uuid_pk()
    wallet_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wallets.id", ondelete="CASCADE"),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    reference_entity: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    reference_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    actor_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        CheckConstraint("kind IN ('credit','debit')", name="ck_wallet_transactions_kind"),
        CheckConstraint(
            "amount > 0 AND balance_after >= 0",
            name="ck_wallet_transactions_amount",
        ),
        Index(
            "ix_wallet_transactions_wallet_id_at", "wallet_id", "at"
        ),
        Index(
            "ix_wallet_transactions_ref", "reference_entity", "reference_id"
        ),
    )


class Referral(Base, TimestampMixin, ActorMixin, SoftDeleteMixin):
    """A referral code issued by one user, optionally redeemed by another."""

    __tablename__ = "referrals"

    id = uuid_pk()
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    referrer_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    referee_user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reward_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default=text("0")
    )
    status: Mapped[str] = mapped_column(
        String(24), nullable=False, server_default=text("'pending'")
    )
    redeemed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("referee_user_id", name="uq_referrals_referee_user_id"),
        CheckConstraint(
            "status IN ('pending','redeemed','expired','cancelled')",
            name="ck_referrals_status",
        ),
        CheckConstraint("reward_amount >= 0", name="ck_referrals_reward_nonneg"),
        Index("ix_referrals_referrer_user_id", "referrer_user_id"),
        Index("ix_referrals_status", "status"),
    )


__all__ = [
    "CustomerProfile",
    "Address",
    "Wallet",
    "WalletTransaction",
    "Referral",
]
