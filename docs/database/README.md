# Database Migrations Log

One document per Alembic revision. Kept in lock-step with `backend/migrations/versions/`.

## Sprint 1.1 (Database Foundation)

| Revision | Title | Doc |
|---|---|---|
| 001 | Extensions and enums | [001-extensions-and-enums.md](001-extensions-and-enums.md) |
| 002 | Identity core | [002-identity-core.md](002-identity-core.md) |
| 003 | Master data | [003-master-data.md](003-master-data.md) |

## Sprint 1.2 (Catalog + Inventory)

| Revision | Title | Doc |
|---|---|---|
| 004 | Catalog (products, variants, images, documents, certifications, price journals) | [004-catalog.md](004-catalog.md) |
| 005 | Inventory + `v_stock_valuation` view | [005-inventory.md](005-inventory.md) |

## Conventions

- Every migration is idempotent on upgrade and fully reversible on downgrade.
- `alembic check` MUST report zero pending ops after every merged revision.
- Data-only migrations use the `dm_*.py` prefix (none in Sprint 1.1).
- Enum lifecycle: created **once** in migration `001`; table columns reference them with `create_type=False`.
- Actor-tracking (`created_by / updated_by / deleted_by`) FKs on master-data tables are added **after** all tables are created in `003`, breaking the circular dependency with `users`.
