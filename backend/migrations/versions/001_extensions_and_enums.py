"""001 — Extensions and enums

Sets up the PostgreSQL primitives every subsequent migration relies on:

* Extensions:  `pgcrypto` (gen_random_uuid), `uuid-ossp` (fallback), `citext`
  (case-insensitive text — reserved for future use), `pg_trgm` (fuzzy search
  on products/customers, materialised in migration 011).
* Enum types:  the full set from `docs/architecture/02-database-schema.md`
  so downstream tables can reference them with `create_type=False`.

Reversible: `downgrade()` drops every enum and extension in reverse order.

Revision ID: 001
Revises: -
Create Date: 2026-02-06
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ENUMS: list[tuple[str, tuple[str, ...]]] = [
    ("user_status", ("invited", "active", "suspended", "deleted")),
    (
        "stock_state",
        ("available", "reserved", "damaged", "returned", "expired"),
    ),
    (
        "stock_move_type",
        (
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
        ),
    ),
    (
        "order_status",
        ("draft", "confirmed", "packed", "shipped", "delivered", "cancelled", "returned"),
    ),
    ("order_source", ("web", "distributor", "pos", "admin_manual")),
    (
        "payment_status",
        (
            "pending",
            "authorized",
            "captured",
            "failed",
            "refunded",
            "partially_refunded",
        ),
    ),
    (
        "invoice_status",
        ("draft", "issued", "void", "paid", "partially_paid"),
    ),
    ("gst_mode", ("intra", "inter", "exempt", "zero")),
    ("kyc_status", ("pending", "submitted", "verified", "rejected")),
]

EXTENSIONS = ["pgcrypto", "uuid-ossp", "citext", "pg_trgm"]


def upgrade() -> None:
    for ext in EXTENSIONS:
        op.execute(f'CREATE EXTENSION IF NOT EXISTS "{ext}"')

    for name, values in ENUMS:
        values_sql = ", ".join(f"'{v}'" for v in values)
        op.execute(
            f"""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{name}') THEN
                    CREATE TYPE {name} AS ENUM ({values_sql});
                END IF;
            END$$;
            """
        )


def downgrade() -> None:
    for name, _ in reversed(ENUMS):
        op.execute(f"DROP TYPE IF EXISTS {name}")
    # Extensions are safe to leave installed — dropping pgcrypto in a shared
    # cluster would break other schemas. We only drop `citext`/`pg_trgm` which
    # were explicitly added here; leave `pgcrypto` + `uuid-ossp` alone.
    for ext in ("pg_trgm", "citext"):
        op.execute(f'DROP EXTENSION IF EXISTS "{ext}"')
