# 006 — Purchase (vendors, PO, GRN, vendor invoices)

_Sprint 1.4 · schema-only slice · reversible._

## Tables introduced

| Table | Purpose |
|---|---|
| `vendors` | Supplier master (code, GSTIN, PAN, contact, payment terms, credit days, currency). |
| `purchase_orders` | PO header: `po_no` (unique), `vendor_id`, `warehouse_id`, `status`, `order_date`, monetary totals. |
| `po_items` | PO line items. UNIQUE(`po_id`, `variant_id`). Tracks `ordered_qty`, `received_qty`, `unit_price`, `tax_rate`, `discount_pct`, `line_total`. |
| `grn` | Goods Receipt Note header. Optionally linked to a PO. Status ∈ {draft, posted, cancelled}. |
| `grn_items` | GRN line items. Optionally linked back to a `po_item` and to a `batch`. Tracks `received_qty`, `damaged_qty`, `unit_cost`. |
| `vendor_invoices` | Vendor-issued invoice. Status ∈ {draft, submitted, approved, paid, void}. UNIQUE(`vendor_id`, `invoice_no`). |

## Backfilled deferred FKs

Sprint 1.2 left two columns on `purchase_price_history` unlinked (deliberately):

- `purchase_price_history.vendor_id` → `vendors(id)` ON DELETE SET NULL
- `purchase_price_history.po_id` → `purchase_orders(id)` ON DELETE SET NULL

Migration 006 attaches both FKs. Both columns remain nullable so imports from
external systems can still land rows without a matching vendor / PO.

## Key CHECK constraints

- `vendors.credit_days >= 0`.
- `purchase_orders.status ∈ {draft, approved, sent, partially_received, received, closed, cancelled}`.
- `purchase_orders.{subtotal, tax_amount, discount_amount, total} >= 0`.
- `po_items.ordered_qty > 0`, `received_qty ∈ [0, ordered_qty]`, `unit_price >= 0`, `discount_pct ∈ [0, 100]`.
- `grn.status ∈ {draft, posted, cancelled}`.
- `grn_items.received_qty > 0`, `damaged_qty ∈ [0, received_qty]`.
- `vendor_invoices.status ∈ {draft, submitted, approved, paid, void}`, all amounts non-negative, `paid_amount ≤ total`.

## Rollback caveats

`downgrade` drops the six new tables in reverse dependency order and detaches the two `purchase_price_history` FKs. Historical vendor/PO references in `purchase_price_history` are preserved as raw UUIDs (columns kept, constraints removed) so re-upgrading later re-attaches the FKs without data loss.
