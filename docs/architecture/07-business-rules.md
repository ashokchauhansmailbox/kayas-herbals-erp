# 07 — Business Rules

_Authoritative source. Product code must obey. Any deviation requires an ADR._

## Inventory
BR-INV-01 Stock is tracked per (variant, warehouse, batch, state). Snapshot is the sum of ledger entries.
BR-INV-02 A movement always transfers qty between two states (e.g. `available → reserved`) or between warehouses (`available@W1 → available@W2`).
BR-INV-03 Reserved stock is created when order status → `confirmed`. Released on `cancelled`; consumed (removed) on `shipped`.
BR-INV-04 A batch nearing expiry (within `shelf_life_days × 0.2` OR 30 days, whichever larger) auto-generates a `near_expiry` alert.
BR-INV-05 An expired batch is moved via `expire` movement into `expired` state; cannot be sold.
BR-INV-06 Damaged units go to `damaged` state via `damage` movement with mandatory reason.
BR-INV-07 Returned units go to `returned` state; QC decides whether they move back to `available` or `damaged`.
BR-INV-08 Negative available stock is forbidden by CHECK constraint on snapshot.
BR-INV-09 Adjustments require a reason code and are audited.

## Billing & GST
BR-BILL-01 Invoice is auto-generated when order → `confirmed` (or manually issued for draft orders).
BR-BILL-02 GST mode:
  - Same state as warehouse (place_of_supply) → CGST + SGST, each = tax/2.
  - Different state → IGST (full tax).
  - Zero-rated / exempt as per HSN.
BR-BILL-03 Each invoice item snapshots `hsn_code`, `gst_rate`, `unit_price`, `product_name` — later product changes never mutate history.
BR-BILL-04 Credit note reduces liability; issued only against an existing invoice; reversal cannot exceed invoice amount.
BR-BILL-05 Debit note increases liability; used for undercharged tax or additional items.
BR-BILL-06 Invoice numbers follow `KH/{FY}/{seq}` (financial year Apr-Mar), monotonically incremented per FY, gap-free.
BR-BILL-07 Void invoice sets `status='void'` and creates a mirror credit note; number is retained.
BR-BILL-08 Financial documents cannot be hard-deleted (trigger raises).
BR-BILL-09 GSTR-1 export includes all issued invoices + credit notes + debit notes for the filing period.

## Stock Movements (auditable events)
BR-MOV-01 GRN posting: `inward` in `available` state.
BR-MOV-02 Order confirm: `reserve` movement decrements `available`, increments `reserved` (same wh, same batch).
BR-MOV-03 Order ship: `outward` movement removes from `reserved`.
BR-MOV-04 Return receipt: `return` movement adds to `returned`.
BR-MOV-05 QC pass: `return`→`available`; QC fail: `return`→`damaged`.
BR-MOV-06 Every movement carries `ref_entity` + `ref_id` for traceability.

## Seller / Distributor allocation
BR-DIST-01 Each distributor belongs to exactly one tier (Silver/Gold/Platinum).
BR-DIST-02 Effective price = variant-specific `distributor_price_lists` if present, else `variant.base_price × (1 − tier.default_discount_pct)`.
BR-DIST-03 A distributor order is rejected if it would push `outstanding_amount + order_total > credit_limit` (unless overridden by Sales/Finance with a note, audited).
BR-DIST-04 Distributors cannot see other distributors' data (RLS + service check).
BR-DIST-05 KYC status must be `verified` before first order.

## Order processing
BR-ORD-01 Order lifecycle: `draft → confirmed → packed → shipped → delivered` with branch to `cancelled` (before shipped) or `returned` (after delivered).
BR-ORD-02 Illegal transitions rejected at service layer.
BR-ORD-03 Order confirm requires: valid address, valid payment method (or COD flag), stock reservation success, invoice generation.
BR-ORD-04 Split shipments allowed; each shipment tracks its own AWB.
BR-ORD-05 Cancellation refunds payment via Razorpay if captured.
BR-ORD-06 Coupon application: validated against dates, min-order, per-user limit, and total usage limit atomically.

## User management
BR-USR-01 Supabase Auth is the sole authentication source; local `users` mirrors identity + status.
BR-USR-02 Email verification mandatory for all internal roles before first login.
BR-USR-03 Customers may browse public catalog; verification required at checkout.
BR-USR-04 Suspended user's sessions are revoked and JWT refresh rejected.
BR-USR-05 The last active Super Admin cannot be deleted or suspended.
BR-USR-06 Password reset uses Supabase-generated tokens; our system logs the event.

## Reporting
BR-RPT-01 Reports use `stock_snapshots` and materialised views for speed; underlying ledger is authoritative.
BR-RPT-02 Every report is role-scoped: distributors see only own data; sub-admins see per-permission scope.
BR-RPT-03 Scheduled reports run at 07:00 IST via Celery beat.
