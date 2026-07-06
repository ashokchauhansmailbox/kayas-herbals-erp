"""Shared PostgreSQL column-type helpers."""

from __future__ import annotations

from sqlalchemy import Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import mapped_column


def uuid_pk():
    """Standard UUID primary key: gen_random_uuid() default (needs pgcrypto)."""
    return mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        nullable=False,
    )


def jsonb_column(nullable: bool = True, default=None):
    return mapped_column(
        JSONB(astext_type=Text()),
        nullable=nullable,
        default=default,
    )


__all__ = ["uuid_pk", "jsonb_column", "PGUUID", "JSONB"]
