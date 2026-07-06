# 001 — Extensions and enums

**Revision**: `001` &nbsp;·&nbsp; **Parent**: root &nbsp;·&nbsp; **Sprint**: 1.1

## Purpose
Prepare the PostgreSQL cluster with the extensions and enum types every downstream migration relies on. Nothing in this migration creates data or tables; it only registers primitives.

## Extensions installed
| Extension | Why |
|---|---|
| `pgcrypto` | `gen_random_uuid()` used as PK default on every table |
| `uuid-ossp` | Fallback UUID generators for legacy code paths |
| `citext` | Reserved for future case-insensitive columns (emails, slugs) |
| `pg_trgm` | Fuzzy search / GIN indexes on catalog + customer tables (used in migration 011) |

## Enum types
Declared verbatim from `docs/architecture/02-database-schema.md`:

- `user_status` — invited · active · suspended · deleted
- `stock_state` — available · reserved · damaged · returned · expired
- `stock_move_type` — inward · outward · transfer_in · transfer_out · adjust_plus · adjust_minus · damage · return · expire · reserve · release
- `order_status` — draft · confirmed · packed · shipped · delivered · cancelled · returned
- `order_source` — web · distributor · pos · admin_manual
- `payment_status` — pending · authorized · captured · failed · refunded · partially_refunded
- `invoice_status` — draft · issued · void · paid · partially_paid
- `gst_mode` — intra · inter · exempt · zero
- `kyc_status` — pending · submitted · verified · rejected

## Reversibility
`downgrade()` drops every enum and the extensions we added exclusively (`pg_trgm`, `citext`). `pgcrypto` and `uuid-ossp` are intentionally **left installed** because they are shared cluster primitives and dropping them can break sibling schemas.

## Verified via
- `alembic upgrade head → downgrade base → upgrade head` (integration test)
- `alembic check` (no drift)
- Enum + extension presence asserted in `tests/test_migrations_cycle.py`

## Notes for future migrations
When a new table column references one of the enums above, use SQLAlchemy `postgresql.ENUM(..., name="user_status", create_type=False)` so Alembic does not attempt to recreate the type.
