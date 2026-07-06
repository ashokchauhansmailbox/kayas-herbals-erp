"""Reusable column mixins composed on every business table.

- `TimestampMixin`  → created_at / updated_at (UTC, auto-set).
- `ActorMixin`      → created_by / updated_by (UUID FK to users, nullable).
- `SoftDeleteMixin` → deleted_at / deleted_by (records are hidden, not purged).
- `VersionMixin`    → optimistic-lock integer counter (bumped by trigger in 012).

Compose in this order so column order in migrations is stable:
    class Order(Base, TimestampMixin, ActorMixin, SoftDeleteMixin, VersionMixin): ...
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
        server_default=func.now(),
    )


class ActorMixin:
    created_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL", use_alter=True),
        nullable=True,
    )
    updated_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL", use_alter=True),
        nullable=True,
    )


class SoftDeleteMixin:
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    deleted_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL", use_alter=True),
        nullable=True,
    )


class VersionMixin:
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    # SQLAlchemy optimistic lock (opt-in per model via __mapper_args__).
    # We do NOT set __mapper_args__ globally because mixins can't safely
    # override subclass mapper args in a composable way. Individual models
    # that require optimistic locking set:
    #   __mapper_args__ = {"version_id_col": version}
