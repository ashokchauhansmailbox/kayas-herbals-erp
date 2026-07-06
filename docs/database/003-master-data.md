# 003 — Master data

**Revision**: `003` &nbsp;·&nbsp; **Parent**: `002` &nbsp;·&nbsp; **Sprint**: 1.1

## Tables created
All ten master-data tables from `docs/architecture/08-master-data.md`, each carrying the standard mixin columns (`created_at / updated_at / created_by / updated_by / deleted_at / deleted_by`).

| Table | Owner role(s) | Key columns |
|---|---|---|
| `units` | Super Admin, Catalog Mgr | `code UNIQUE`, `name`, `base_unit_id → units.id`, `conversion_factor NUMERIC(18,6)`, `is_active` |
| `gst_rates` | Super Admin, Finance | `rate NUMERIC(5,2) UNIQUE`, `description`, `effective_from`, `effective_to?`, `is_active` |
| `hsn_codes` | Super Admin, Catalog Mgr, Finance | `code UNIQUE`, `description`, `default_gst_rate_id → gst_rates.id (RESTRICT)`, `is_active` |
| `categories` | Catalog Mgr | `name`, `slug UNIQUE`, `parent_id → categories.id`, `image_url`, `sort_order`, `is_active` |
| `brands` | Catalog Mgr | `name UNIQUE`, `slug UNIQUE`, `logo_url`, `manufacturer`, `country_of_origin`, `is_active` |
| `warehouses` | Super Admin, Inventory | `code UNIQUE`, `name`, `gstin`, `address JSONB`, `is_active`, `version` (optimistic lock) |
| `payment_terms` | Finance | `code UNIQUE`, `name`, `days INT`, `is_active` |
| `tax_rules` | Finance | `code UNIQUE`, `name`, `mode gst_mode`, `components JSONB`, `effective_from`, `effective_to?`, `is_active` |
| `transporters` | Sales, Inventory | `name UNIQUE`, `contact JSONB`, `gstin`, `rate_card_url`, `is_active` |
| `courier_partners` | Sales, Support | `code UNIQUE`, `name`, `api_config JSONB`, `is_active` |

## Indexes
- Per-table `ix_<table>_code` (or `_slug` where applicable)
- `ix_gst_rates_effective_from`
- `ix_categories_parent_id`

## Foreign-key strategy
The circular dependency between actor columns (`created_by / updated_by / deleted_by → users.id`) and the tables themselves is broken by:

1. Creating **all** master-data tables first with actor columns declared but no FK constraint.
2. Adding the FK constraints in a second pass (`_add_actor_fks(...)`), all pointing at `users.id` with `ON DELETE SET NULL`.

This mirrors the pattern used for `users.deleted_by` in migration 002 (`use_alter=True`).

## Special constraints & types
- `units.base_unit_id` self-refs `units.id` with `ON DELETE SET NULL` (converting base unit to null preserves child rows).
- `categories.parent_id` self-refs with `ON DELETE SET NULL` for tree flattening on parent removal.
- `hsn_codes.default_gst_rate_id → gst_rates.id` uses `ON DELETE RESTRICT` — a GST slab can't be removed while HSN codes reference it.
- `tax_rules.mode` uses the pre-declared `gst_mode` enum with `create_type=False`.
- `warehouses` carries a `version` column (optimistic lock) because warehouse stock coordination is high-contention.
- JSONB columns: `warehouses.address`, `tax_rules.components`, `transporters.contact`, `courier_partners.api_config`.

## Downgrade
Actor FKs are dropped first, then tables in reverse creation order. The `gst_mode` enum is **not** dropped — it belongs to migration 001.

## Business-rule anchors
- BR-BILL-02 — Tax rules feed CGST/SGST vs IGST decisions at invoice posting.
- BR-BILL-03 — Effective-dated `gst_rates` + `tax_rules` snapshot into `invoice_items` at posting time.
- Master-data soft-deletion — see the FK check + service layer error pattern in `docs/architecture/08-master-data.md`.

## Verified via
- Round-trip: `upgrade head → downgrade base → upgrade head`
- `alembic check` (no drift)
- Presence + shape asserted in `tests/test_models_schema.py`

## Deferred to later sprints
- Actual seed data (units, GST rates, HSN codes, categories, brand "Kaya's Herbals", warehouse "KH-Bangalore-Main", payment terms, tax rules, courier partners) — Sprint 1.6.
- CRUD UI + endpoints — Sprint 2.
