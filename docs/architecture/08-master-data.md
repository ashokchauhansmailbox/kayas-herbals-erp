# 08 — Master Data Module

Master data is the reference layer every transactional module depends on. Managed by Super Admin only (plus specific roles below). Every table gets full CRUD UI in Sprint 2.

| Table | Purpose | Key columns | Owning role |
|---|---|---|---|
| `units` | Units of measure | `code UNIQUE` (pcs, g, kg, ml, l, box, strip, bottle), `name`, `base_unit_id NULL`, `conversion_factor NUMERIC` | Super Admin, Catalog Mgr |
| `gst_rates` | GST slabs | `rate NUMERIC(5,2) UNIQUE` (0, 5, 12, 18, 28), `description`, `effective_from`, `effective_to NULL` | Super Admin, Finance |
| `hsn_codes` | HSN classification | `code UNIQUE`, `description`, `default_gst_rate_id FK`, `is_active` | Super Admin, Catalog Mgr, Finance |
| `categories` | Product taxonomy tree | `name`, `slug UNIQUE`, `parent_id NULL`, `image_url`, `sort_order`, `is_active` | Catalog Mgr |
| `brands` | Brand master | `name UNIQUE`, `slug UNIQUE`, `logo_url`, `manufacturer`, `country_of_origin`, `is_active` | Catalog Mgr |
| `warehouses` | Storage locations | `code UNIQUE`, `name`, `gstin`, `address_json`, `is_active` | Super Admin, Inventory Mgr |
| `payment_terms` | Credit terms for distributors / vendors | `code UNIQUE` (NET7, NET15, NET30, ADV, COD), `name`, `days INT`, `is_active` | Finance |
| `tax_rules` | Tax composition rules | `code UNIQUE`, `name`, `mode gst_mode`, `components JSONB` (e.g., CGST 9 + SGST 9), `effective_from`, `effective_to NULL` | Finance |
| `transporters` | Freight / LTL vendors | `name UNIQUE`, `contact_json`, `gstin`, `rate_card_url`, `is_active` | Sales, Inventory |
| `courier_partners` | Last-mile couriers | `code UNIQUE` (Delhivery, Bluedart, DTDC, IndiaPost, Shiprocket-*), `name`, `api_config_json`, `is_active` | Sales, Support |

## Cross-cutting behaviour
- Every master table supports Search / Filter / Sort / Pagination out of the box (via shared `<DataTable/>`).
- Every master table has Excel + PDF export.
- Every master table is audited (before/after JSONB).
- Every master table is soft-deletable; deletion is blocked if referenced by an active transaction (FK check + service layer error).
- Master data changes emit an `activity_log` event so downstream caches invalidate.

## Effective-dating
`gst_rates` and `tax_rules` are effective-dated: transactions snapshot the rate at posting time (see BR-BILL-03).

## Seeds
Sprint 1 seed data includes:
- Units: 8 rows
- GST rates: 5 rows
- HSN codes: ~40 seed rows for herbal categories (Ayurveda, Cosmetics, Food supplements)
- Categories: Powders, Capsules, Teas, Skincare, Oils, Herbs (with icons)
- Brand: "Kaya's Herbals"
- Warehouse: "KH-Bangalore-Main"
- Payment terms: 5 codes
- Tax rules: Intra-GST-standard, Inter-GST-standard, Exempt, Zero-rated
- Courier partners: Delhivery, Bluedart, IndiaPost (config keys blank until keys provided)
