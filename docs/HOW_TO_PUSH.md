# How to publish Sprint 1.1 + 1.2 to GitHub

The Emergent runtime cannot execute git push / PR-create actions on your
behalf. Use the **"Save to GitHub"** button in the chat input to commit
the current workspace state to
`github.com/ashokchauhansmailbox/kayas-herbals-erp`.

## Recommended flow

### 1. Commit Sprint 1.1 to its own branch + PR
- Click **Save to GitHub**.
- Branch name: `sprint/1.1-database-foundation`.
- Message: `Sprint 1.1 — Database Foundation (SQLAlchemy + Alembic 001–003)`.
- After the push, open the repo on GitHub and click **Compare & pull request**.
  - Base: `main` &nbsp;·&nbsp; Compare: `sprint/1.1-database-foundation`.
  - Title: `Sprint 1.1 — Database Foundation`.
  - Body: paste the "8-item Sprint Review" section from
    `docs/sprints/S1.1.md` (or copy the concise version below).

### 2. Commit Sprint 1.2 to its own branch + PR
Because Sprint 1.2 builds on 1.1, you have two options:

**Option A (cleanest history — recommended)**
- Wait for the Sprint 1.1 PR to merge into `main`.
- Then Save to GitHub with branch `sprint/1.2-catalog-inventory`.
- GitHub will offer a PR against `main` containing only the 1.2 diff.

**Option B (parallel review)**
- Save to GitHub with branch `sprint/1.2-catalog-inventory`.
- Open the PR against `sprint/1.1-database-foundation` (not `main`). GitHub
  will automatically re-target once 1.1 is merged.

## Sprint 1.1 PR summary (paste as PR body)
> **Sprint 1.1 — Database Foundation**
> - SQLAlchemy base/session/mixins/types (`app/db/`)
> - Identity models (9 tables) — users, roles, permissions, sessions, invitations, audit/activity logs
> - Master-data models (10 tables) — units, gst_rates, hsn_codes, categories, brands, warehouses, payment_terms, tax_rules, transporters, courier_partners
> - Alembic migrations 001 (extensions + 9 enums), 002 (identity core), 003 (master data)
> - Per-migration docs `docs/database/001-003.md`
> - Health endpoints `/api/v1/health/{live,ready,db}`
> - Round-trip verified: `alembic upgrade head → downgrade base → upgrade head`; `alembic check` = zero drift.
> - CI workflow at `.github/workflows/ci.yml` (ruff, mypy, pytest, alembic cycle, OpenAPI drift).
> - OpenAPI baseline committed at `docs/api/openapi.{json,yaml}`.
> - 39 pytest cases green.

## Sprint 1.2 PR summary (paste as PR body)
> **Sprint 1.2 — Catalog + Inventory**
> - Catalog models: `Product`, `ProductVariant`, `ProductImage`, `ProductDocument`, `Certification`, `ProductPriceHistory`, `PurchasePriceHistory` (migration 004).
> - Inventory models: `Batch`, `StockAdjustment`, `StockTransfer`, `StockTransferItem`, `StockLedger`, `StockSnapshot`, `StockAlert` (migration 005) + `v_stock_valuation` view.
> - CHECK constraints: `qty <> 0` (ledger), `qty > 0` (transfer item), `from ≠ to` (transfer), `available qty ≥ 0` (snapshot).
> - Functional unique index on `stock_snapshots (variant, warehouse, COALESCE(batch, zero-uuid), state)`.
> - Per-migration docs `docs/database/004-catalog.md`, `005-inventory.md`.
> - 79 pytest cases green (schema contract + migration cycle + integration/CRUD/CHECK/view).
> - Reproducibility verified against a fresh Postgres + venv.

## After both PRs merge
CI on `main` will run the full pipeline (ruff, mypy, pytest, alembic
cycle, OpenAPI drift) automatically. Any subsequent PR that breaks
schema, adds a route without regenerating `docs/api/openapi.{json,yaml}`,
or introduces model↔migration drift will fail before merge.
