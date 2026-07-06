# 007 — Distributor + Customer

_Sprint 1.4 · schema-only slice · reversible._

## Tables introduced

### Distributor side (B2B)

| Table | Purpose |
|---|---|
| `distributor_tiers` | Tier catalogue (Silver, Gold, …). `code` unique, `default_discount_pct ∈ [0, 100]`, `sort_order`. |
| `distributors` | B2B account. `code` unique, business + legal name, GSTIN/PAN, credit limit + days, `current_balance`, `kyc_status ∈ {pending, submitted, verified, rejected}`, `primary_user_id → users.id`. |
| `price_lists` | Global / tier / distributor scoped price list. Scope-consistency `CHECK` enforces exactly one of `tier_id` or `distributor_id` (or neither for global). |
| `price_list_items` | UNIQUE(`price_list_id`, `variant_id`). Tracks `price`, `min_qty`, optional `max_qty`. |
| `kyc_documents` | Distributor-scoped KYC uploads. Status ∈ {submitted, verified, rejected}, `verified_by → users.id`. |

### Customer side (B2C)

| Table | Purpose |
|---|---|
| `customer_profiles` | 1:1 extension of `users` — phone, DOB, gender, avatar, marketing opt-in, preferred language. UNIQUE(`user_id`). |
| `addresses` | User-owned postal addresses. `label ∈ {billing, shipping, other}`. **Partial unique index** `uq_addresses_default_per_user_label` enforces at most one default per (user, label) among active, non-deleted rows. |
| `wallets` | 1:1 with users. `balance >= 0` (DB CHECK). UNIQUE(`user_id`). |
| `wallet_transactions` | Append-only wallet ledger. `kind ∈ {credit, debit}`, `amount > 0`, `balance_after >= 0`, reference-entity pointer for the source event. |
| `referrals` | Referrer→referee mapping. `code` unique, `referee_user_id` unique (a person can only be referred once). Status ∈ {pending, redeemed, expired, cancelled}. |

## Business invariants captured at the DB

- BR-DIST-01 — distributor code globally unique.
- BR-DIST-02 — KYC status enumerated at CHECK.
- BR-DIST-03 — Price-list scope consistency (see `ck_price_lists_scope_consistency`).
- BR-DIST-04 — Distributor credit values non-negative.
- BR-CUST-01 — Customer profile 1:1 with users.
- BR-CUST-02 — At most one default address per (user, label).
- BR-CUST-03 — Wallet balance non-negative.
- BR-CUST-04 — Wallet transactions append-only (no `updated_at` / `deleted_at`).
- BR-CUST-05 — Each referee is uniquely referred.

## Rollback caveats

`downgrade` drops the ten new tables in reverse dependency order. The partial
unique index on `addresses` is dropped explicitly (`DROP INDEX IF EXISTS ...`)
because Alembic autogenerate cannot describe partial indexes from a `WHERE`
predicate on a plain unique index.
