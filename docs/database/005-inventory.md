# 005 — Inventory + stock valuation view

**Revision**: `005` &nbsp;·&nbsp; **Parent**: `004` &nbsp;·&nbsp; **Sprint**: 1.2

## Tables created

| Table | Purpose | Key columns |
|---|---|---|
| `batches` | Lot-level identity | `variant_id → product_variants.id (RESTRICT)`, `batch_no`, `mfg_date`, `expiry_date`, `qty_manufactured NUMERIC(14,4)`, `cost_per_unit NUMERIC(14,4)`, `supplier_ref`, `notes`, `version` · UNIQUE(`variant_id`, `batch_no`) |
| `stock_adjustments` | Header for manual adjustments | `reference_no UNIQUE`, `warehouse_id`, `reason_code`, `notes`, `status`, `posted_at`, `posted_by`, `version` |
| `stock_transfers` | Header for inter-warehouse transfers | `reference_no UNIQUE`, `from_warehouse_id`, `to_warehouse_id`, `status`, `dispatched_at`, `received_at`, `notes`, `version` · CHECK: from ≠ to |
| `stock_transfer_items` | Line items on a transfer | `transfer_id → stock_transfers.id (CASCADE)`, `variant_id`, `batch_id?`, `qty` · CHECK: qty > 0 |
| `stock_ledger` | Append-only movement journal | `variant_id`, `warehouse_id`, `batch_id?`, `move_type` (enum), `qty`, `state_from?` (enum), `state_to` (enum), `ref_entity`, `ref_id`, `reason`, `at`, `actor_id` · CHECK: qty ≠ 0 |
| `stock_snapshots` | Materialised balance | `variant_id`, `warehouse_id`, `batch_id?`, `state` (enum), `qty`, `last_movement_id → stock_ledger.id (SET NULL)` · CHECK: available qty ≥ 0 · functional UQ index over `COALESCE(batch_id, zero-uuid)` |
| `stock_alerts` | Low-stock + near-expiry alerts | `alert_type`, `severity`, `variant_id?`, `warehouse_id?`, `batch_id?`, `threshold_value`, `current_value`, `message`, `raised_at`, `resolved_at?`, `resolved_by` |

## Indexes
- `ix_batches_variant_id`, `ix_batches_expiry_date`
- `ix_stock_adjustments_warehouse_id`, `ix_stock_adjustments_status`
- `ix_stock_transfers_from_warehouse_id`, `ix_stock_transfers_to_warehouse_id`, `ix_stock_transfers_status`
- `ix_stock_transfer_items_transfer_id`
- `ix_stock_ledger_variant_wh_at (variant_id, warehouse_id, at)`, `ix_stock_ledger_batch_id`, `ix_stock_ledger_ref (ref_entity, ref_id)`, `ix_stock_ledger_move_type (move_type, at)`
- `ix_stock_snapshots_state`, `ix_stock_snapshots_variant_wh`, functional `uq_stock_snapshots_natural_key`
- `ix_stock_alerts_alert_type (alert_type, raised_at)`, `ix_stock_alerts_variant_id`, `ix_stock_alerts_warehouse_id`, `ix_stock_alerts_open (resolved_at)`

## CHECK constraints
- `ck_stock_transfers_different_warehouses` — source/destination warehouses must differ.
- `ck_stock_transfer_items_qty_positive` — transfer line qty > 0.
- `ck_stock_ledger_qty_nonzero` — ledger row qty ≠ 0 (BR-INV-02).
- `ck_stock_snapshots_available_nonnegative` — `state='available' ⇒ qty ≥ 0` (BR-INV-08).

## Materialised view: `v_stock_valuation`
```sql
CREATE OR REPLACE VIEW v_stock_valuation AS
SELECT
    s.variant_id, s.warehouse_id, s.batch_id, s.state, s.qty,
    b.cost_per_unit,
    (s.qty * COALESCE(b.cost_per_unit, 0))::NUMERIC(20, 4) AS total_value,
    b.batch_no, b.mfg_date, b.expiry_date,
    CASE WHEN b.expiry_date IS NULL THEN NULL
         ELSE (b.expiry_date - CURRENT_DATE) END AS days_to_expiry
FROM stock_snapshots s
LEFT JOIN batches b ON b.id = s.batch_id
WHERE s.qty <> 0;
```

Consumers:
- Inventory dashboard KPIs (Sprint 2 UI).
- Warehouse valuation report.
- Near-expiry / expired analytics.

## Business-rule anchors
- **BR-INV-01** — snapshot key is `(variant, warehouse, batch, state)`. Enforced by the functional unique index.
- **BR-INV-02** — every ledger row transfers qty between two states or two warehouses. Movement type + `state_from` + `state_to` capture both intents.
- **BR-INV-04** — near-expiry threshold (`shelf_life_days × 0.2 OR 30 days, whichever larger`) drives `stock_alerts.alert_type = 'near_expiry'`.
- **BR-INV-05** — expired batches move via `expire` → `expired` state; cannot be sold.
- **BR-INV-06** — damaged units move via `damage` movement into `damaged` state (mandatory reason).
- **BR-INV-08** — negative `available` qty forbidden — enforced by CHECK.
- **BR-INV-09** — adjustments require a reason code (`stock_adjustments.reason_code` NOT NULL).

## Downgrade
`DROP VIEW v_stock_valuation` first, then actor FKs, then tables in reverse creation order.

## Verified via
- Round-trip: `upgrade head → downgrade base → upgrade head`
- `alembic check` (no drift)
- View existence + row shape asserted in `tests/test_migrations_cycle.py` and `tests/test_catalog_inventory.py::test_stock_valuation_view_computes_total`.
- CHECK constraints exercised via `IntegrityError` in `tests/test_catalog_inventory.py`.
