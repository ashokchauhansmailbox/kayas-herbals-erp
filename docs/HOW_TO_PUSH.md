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

### 2. Commit Sprint 1.2 to its own branch + PR
- Branch name: `sprint/1.2-catalog-inventory`.
- Message: `Sprint 1.2 — Catalog + Inventory (migrations 004, 005 + v_stock_valuation view)`.

### 3. Commit Sprint 1.3 to its own branch + PR
- Branch name: `sprint/1.3-auth-rbac-audit-seeds-routes`.
- Message: `Sprint 1.3 — Auth + RBAC + Audit + Seeds + Route Foundations`.

For all three, after the push, open the repo on GitHub and click **Compare & pull request**.
Base: `main` &nbsp;·&nbsp; Compare: `<sprint-branch>`. Paste the corresponding
"PR summary" section below as the PR body.

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

## Sprint 1.3 PR summary (paste as PR body)
> **Sprint 1.3 — Authentication + RBAC + Audit + Seeds + Route Foundations**
> - `app/core/security.py` — Supabase HS256 JWT verifier (signature, aud, exp, sub validation).
> - `app/deps.py` — `get_db`, `get_current_user`, `require("perm.code")`, `request_id` FastAPI dependencies.
> - `app/services/auth_service.py` — resolves local user + effective roles/permissions, session tracking via `sessions.jti` + `revoked_at`.
> - `app/services/audit_service.py` — `AuditContext` (before/after → deepdiff) writes audit rows in the same tx as the mutation.
> - Seeds: 89 permissions, 9 system roles, full role→permission mapping, 8 units, 5 GST rates, 12 HSN codes, 6 categories, 1 brand (Kaya's Herbals), 1 warehouse (KH-BLR-MAIN), 5 payment terms, 4 tax rules, 5 courier partners. Fully idempotent (`python -m app.seeds.run` runs safely N times).
> - Pydantic schemas: `common.py`, `auth.py`, `admin.py`.
> - Routes (18 endpoints): `/auth/me|sessions|logout`, `/users`, `/roles`, `/permissions`, `/invitations`, `/audit/logs|activity`.
> - Postman collection baseline at `docs/api/postman_collection.json` (23 requests) — CI drift-checked alongside OpenAPI.
> - Auth tests: bearer missing/malformed, expired, wrong-audience, tampered signature, wrong secret, invalid subject, suspended user, revoked session.
> - RBAC tests: every seeded permission installed; every seeded role has expected permission set; forbidden calls return `rbac.forbidden`.
> - Audit + OWASP tests: role update writes diff, /me writes activity, SQLi input, IDOR, no-internals leak, `alg=none` rejected.
> - 109 pytest cases green. `alembic check` = zero drift. `check_openapi_drift.py` clean for all three artifacts. Reproducibility verified against a fresh Postgres + fresh venv.

## After both PRs merge
CI on `main` will run the full pipeline (ruff, mypy, pytest, alembic
cycle, OpenAPI drift) automatically. Any subsequent PR that breaks
schema, adds a route without regenerating `docs/api/openapi.{json,yaml}`,
or introduces model↔migration drift will fail before merge.
