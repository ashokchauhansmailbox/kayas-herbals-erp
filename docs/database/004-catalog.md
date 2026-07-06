# 004 — Catalog

**Revision**: `004` &nbsp;·&nbsp; **Parent**: `003` &nbsp;·&nbsp; **Sprint**: 1.2

## Tables created

| Table | Purpose | Key columns |
|---|---|---|
| `products` | SKU family / product master | `sku UNIQUE`, `slug UNIQUE`, `category_id → categories.id (RESTRICT)`, `brand_id → brands.id (RESTRICT)`, `hsn_code_id → hsn_codes.id (RESTRICT)`, `default_unit_id → units.id (RESTRICT)`, `fssai_licence`, `ayush_licence`, `manufacturer`, `country_of_origin`, `shelf_life_days`, `storage_instructions`, `description`, `benefits`, `ingredients`, `dosage`, `is_active`, `version` (opt-lock) |
| `product_variants` | Shipped SKUs (size / potency) | `product_id → products.id (CASCADE)`, `sku UNIQUE`, `variant_name`, `mrp NUMERIC(14,2)`, `base_price NUMERIC(14,2)`, `pack_size NUMERIC(14,4)`, `unit_id → units.id (RESTRICT)`, `barcode UNIQUE`, `qr_code_url`, `is_active`, `version` |
| `product_images` | Variant-scoped media | `variant_id → product_variants.id (CASCADE)`, `url`, `alt`, `sort_order`, `is_primary` |
| `product_documents` | Spec sheets, brochures, MSDS, lab reports | `product_id → products.id (CASCADE)`, `doc_type`, `title`, `file_url`, `mime_type`, `version_label`, `is_public` |
| `certifications` | AYUSH / FSSAI / organic / lab | `product_id → products.id (CASCADE)`, `type`, `number`, `issued_by`, `issued_on`, `valid_until`, `file_url` |
| `product_price_history` | Selling-price journal (append-only) | `variant_id → product_variants.id (CASCADE)`, `price`, `mrp?`, `effective_from`, `effective_to?`, `changed_by → users.id (SET NULL)`, `reason`, `at` |
| `purchase_price_history` | Buy-price journal (append-only) | `variant_id`, `vendor_id?` (FK deferred), `po_id?` (FK deferred), `price`, `currency`, `quantity`, `at`, `recorded_by → users.id (SET NULL)` |

## Indexes
- `ix_products_sku`, `ix_products_slug`, `ix_products_category_id`, `ix_products_brand_id`, `ix_products_is_active`
- `ix_product_variants_product_id`, `ix_product_variants_sku`, `ix_product_variants_barcode`
- `ix_product_images_variant_id (variant_id, sort_order)`
- `ix_product_documents_product_id`, `ix_product_documents_doc_type`
- `ix_certifications_product_id`, `ix_certifications_type`, `ix_certifications_valid_until`
- `ix_product_price_history_variant_id (variant_id, effective_from)`
- `ix_purchase_price_history_variant_id (variant_id, at)`, `ix_purchase_price_history_vendor_id`

## Journals — append-only shape
`product_price_history` and `purchase_price_history` intentionally omit `updated_at` and `deleted_at`. Rows are inserted, never mutated. Sprint 1.5 adds a database trigger that blocks UPDATE/DELETE (BR-BILL-08 pattern applied to price journals).

## Deferred FKs
`purchase_price_history.vendor_id` and `.po_id` are UUID columns without a FK constraint. Sprint 1.3 (Purchase) will add:

```sql
ALTER TABLE purchase_price_history
  ADD CONSTRAINT fk_purchase_price_history_vendor_id_vendors
    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE SET NULL,
  ADD CONSTRAINT fk_purchase_price_history_po_id_purchase_orders
    FOREIGN KEY (po_id) REFERENCES purchase_orders(id) ON DELETE SET NULL;
```

## Downgrade
Actor FKs dropped first, then tables in reverse creation order.

## Business-rule anchors
- Sprint 1.5 will add `products.tsv` (GIN) for full-text search — deferred to migration 011.
- BR-BILL-03 — invoice items snapshot HSN + GST rate at posting time; `products.hsn_code_id` is the *current* mapping and can change over time, but invoices never mutate.

## Verified via
- Round-trip: `upgrade head → downgrade base → upgrade head`
- `alembic check` (no drift)
- `tests/test_models_schema.py`, `tests/test_catalog_inventory.py` (product CRUD, journal append, uniqueness).
