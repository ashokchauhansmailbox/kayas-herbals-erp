# Kaya BOS — Product Requirements Document

## Original Problem Statement
Kaya BOS (Business Operating System) is a production-grade **ERP + Inventory + Billing + Distributor + E-commerce** platform for Kaya's Herbals. Rebuilt from the earlier MongoDB MVP as a clean-architecture modular monolith backed by PostgreSQL/Supabase, FastAPI (SQLAlchemy 2 async + Alembic), Pydantic v2, and a React/TypeScript frontend.

Repository: https://github.com/ashokchauhansmailbox/kayas-herbals-erp

## User Personas
1. **Super Admin / Ops** — configures master data, RBAC, feature flags; oversees compliance (GST, AYUSH, FSSAI).
2. **Catalog Manager** — products, HSN, brands, images, certifications.
3. **Inventory Manager** — warehouses, batches, stock states, transfers, alerts.
4. **Sales / Finance Manager** — orders, invoices, credit/debit notes, payments, GST filings.
5. **Distributor / Seller** — tiered price lists, own KYC, own orders, own ledger.
6. **Retail Customer** — public storefront browsing, checkout, wallet, returns.

## Tech stack (locked at Sprint 0)
- Backend: **FastAPI**, **SQLAlchemy 2.x async**, **Alembic**, **Pydantic v2**, **PyJWT** (Supabase HS256).
- Database: **PostgreSQL 16** (Supabase in staging/prod).
- Frontend: **React 19 + Vite + TypeScript + Tailwind + Shadcn/UI + TanStack Query + Zustand + Zod** (per `docs/DECISIONS.md`).
- Infrastructure: Docker (dev), Vercel (frontends), Railway/Render (backend), Supabase (Auth+DB+Storage), Upstash Redis.
- Payments: **Razorpay**. Email: **Resend**. WhatsApp: **WhatsApp Cloud API**.

## Architecture references
- `docs/architecture/01-database-erd.md` — full ER diagram.
- `docs/architecture/02-database-schema.md` — every table/column/index.
- `docs/architecture/03-sqlalchemy-alembic.md` — model layout + migration plan.
- `docs/architecture/04-rls-policies.md` — Supabase RLS as defence-in-depth.
- `docs/architecture/05-rbac.md` — capability-based RBAC + permission matrix.
- `docs/architecture/06-audit-activity.md` — audit vs activity log architecture.
- `docs/architecture/07-business-rules.md` — invariants (BR-INV-*, BR-BILL-*, BR-DIST-*, BR-ORD-*, BR-USR-*, BR-RPT-*).
- `docs/architecture/08-master-data.md` — reference-data ownership and seeds.
- `docs/DECISIONS.md` — frozen stack + brand tokens.

## Implementation log

### Sprint 0 (2026-01) — Foundation
Monorepo skeleton, brand tokens, `.env.example`, DECISIONS.md, architecture docs 01-08. Every downstream sprint dependency has a clear next step.

### Sprint 1 (2026-01) — scaffolding-only
`docker-compose.yml`, `backend/Dockerfile`, `requirements.txt`, `.env.example`. `backend/app/core/` (Settings, structlog logging, unified error envelope). `backend/app/main.py` with FastAPI + CORS + `/api/v1` mount + OpenAPI at `/api/v1/docs`.

Sprint 1 was then split into sub-sprints 1.1 → 1.7 (see `docs/sprints/S1.md`).

### Sprint 1.1 (2026-02-06) — Database Foundation ✅

- SQLAlchemy `Base` + naming convention (`app/db/base.py`).
- Async engine + session factory with `configure_engine()` test hook (`app/db/session.py`).
- Mixins: `TimestampMixin`, `ActorMixin`, `SoftDeleteMixin`, `VersionMixin` (`app/db/mixins.py`).
- Postgres type helpers: `uuid_pk()`, `jsonb_column()` (`app/db/types.py`).
- **Identity models** (`app/models/identity.py`): users, roles, permissions, role_permissions, user_roles, sessions, user_invitations, audit_logs, activity_logs.
- **Master-data models** (`app/models/master_data.py`): units, gst_rates, hsn_codes, categories, brands, warehouses, payment_terms, tax_rules, transporters, courier_partners.
- Alembic setup (`alembic.ini`, `migrations/env.py`, `migrations/script.py.mako`) — async-aware, `-x db_url=` override.
- Migrations `001` (extensions + 9 enums), `002` (identity core — 9 tables), `003` (master data — 10 tables).
- Per-migration docs under `/docs/database/`.
- Health endpoints (`/api/v1/health/live`, `/ready`, `/db`).

Round-trip verified: `alembic upgrade head → downgrade base → upgrade head`. `alembic check` reports zero drift.

### Sprint 1.1.1 (2026-02-06) — CI & OpenAPI baseline

- `.github/workflows/ci.yml` — ruff, mypy, pytest, alembic cycle, OpenAPI drift check as CI gates.
- OpenAPI baseline committed at `docs/api/openapi.{json,yaml}`; regenerated via `scripts/generate_openapi.py`, verified via `scripts/check_openapi_drift.py`.
- `backend/.env.example`, `backend/mypy.ini`, `infra/postgres-init/01-create-test-db.sql`.
- `conftest.py` refactored to give each pytest-xdist worker its own database (avoids collisions between the migration-cycle suite and integration suites).

### Sprint 1.2 (2026-02-06) — Catalog + Inventory ✅ Complete

- **Catalog models** (`app/models/catalog.py`): `Product`, `ProductVariant`, `ProductImage`, `ProductDocument`, `Certification`, `ProductPriceHistory`, `PurchasePriceHistory`.
- **Inventory models** (`app/models/inventory.py`): `Batch`, `StockAdjustment`, `StockTransfer`, `StockTransferItem`, `StockLedger`, `StockSnapshot`, `StockAlert`.
- Migration `004` (catalog — 7 tables), migration `005` (inventory — 7 tables + `v_stock_valuation` view).
- CHECK constraints: `qty <> 0` on ledger, `qty > 0` on transfer items, `from ≠ to` on transfers, `available qty ≥ 0` on snapshots.
- Functional unique index on `stock_snapshots (variant, warehouse, COALESCE(batch, zero-uuid), state)`.
- Per-migration docs `docs/database/004-catalog.md`, `005-inventory.md`.
- 79 pytest cases green (schema contract + migration cycle + integration/CRUD/CHECK/view assertions).

## Backlog

### P0 — next up
- **Sprint 1.4 — Purchase + Distributor + Customer**: `purchase.py` (vendors, purchase_orders, po_items, grn, grn_items, vendor_invoices) + `distributor.py` (tiers, price lists, distributors, kyc_documents, customer_ledger) + `customer.py` (profiles, addresses, wallets, referrals). Migrations `006`, `007` + data migration to install `purchase_price_history.vendor_id/po_id` FKs.

### P1
- Sprint 1.5 — Orders + Billing + Payments · migrations `008`, `009`.
- Sprint 1.6 — Marketing + Support + Settings + indexes/views/triggers (append-only journal triggers, hard-delete guard on financial docs) · migrations `010`, `011`, `012`.

### P2
- Sprint 1.7 — Ops runbooks (Backup, DR, Migration, Rollback, Restore, Version-Upgrade) + final OpenAPI + Postman snapshot + release readiness review.

### Sprint 1.4 (2026-02-06) — Purchase + Distributor + Customer ✅ Complete (Quality Gate 9.0/10)

- **Migration 006 (purchase)** — vendors, purchase_orders, po_items, grn, grn_items, vendor_invoices; backfilled `purchase_price_history.vendor_id`/`po_id` FKs.
- **Migration 007 (distributor + customer)** — distributor_tiers, distributors, price_lists, price_list_items, kyc_documents, customer_profiles, addresses, wallets, wallet_transactions, referrals.
- **Models** — 16 new mapped classes across `purchase.py` / `distributor.py` / `customer.py`.
- **Routes** — 6 new resource groups (`/vendors`, `/distributor-tiers`, `/distributors` + `/{id}/kyc`, `/me/profile`, `/me/addresses`, `/me/wallet`). All mutating routes RBAC-guarded and audit-wrapped.
- **Tests** — 17 new (5 purchase + 6 distributor + 6 customer) — grand total **164 pytest cases**, ~12 s.
- **Fixes shipped alongside:** `test_migrations_cycle::clean_test_db` teardown now re-seeds; validation handler now sanitises Pydantic `field_validator` errors via `jsonable_encoder`.

### Sprint 1.3 (2026-02-06) — Auth + RBAC + Audit + Seeds + Route Foundations ✅ Complete (Quality Gate passed)

- **Security core** (`app/core/security.py`): HS256 JWT verify against SUPABASE_JWT_SECRET, `mint_token()` for tests.
- **Dependencies** (`app/deps.py`): `get_db`, `get_token_claims`, `get_current_user`, `require("perm.code")`, `request_id`.
- **AuthService** — resolves local user, auto-provisions from Supabase JWT, honours suspension/deletion, tracks `sessions.jti` + `revoked_at`.
- **AuditContext** — before/after JSONB + deepdiff, same tx as mutation. `log_activity()` for read events.
- **Seeds**: 89 permissions, 9 system roles, full role→permission mapping, 8 units, 5 GST rates, 12 HSN codes, 6 categories, 1 brand, 1 warehouse, 5 payment terms, 4 tax rules, 5 courier partners. Fully idempotent.
- **Schemas**: `common.py`, `auth.py`, `admin.py` (ORMModel, Page[T], MeOut, RoleOut, InvitationOut, AuditLogOut, ...).
- **Routes** (18 v1 endpoints): `/auth/me|sessions|logout`, `/users`, `/roles`, `/permissions`, `/invitations`, `/audit/logs|activity`.
- **Postman baseline** at `docs/api/postman_collection.json` (23 requests, 7 folders) — CI drift-checked alongside OpenAPI.
- **CI extended**: seed idempotency (×2) + Docker Compose smoke boot job.
- Tests: 30 new (11 auth + 9 RBAC + 10 audit/OWASP) — grand total **109 pytest cases green**.

### Sprint 1.3 Quality Gate (2026-02-06) ✅ CLOSED

Comprehensive verification pass (see `docs/sprints/S1.3_QUALITY_GATE.md`). Overall production-readiness: **9.0 / 10**.

Fixes applied and verified by the testing agent (`/app/test_reports/iteration_{1,2}.json`):
1. 🔴 **Supervisor was booting the legacy `server.py` (Mongo MVP)** → repointed `[program:backend]` to `app.main:app`; new v1 API is now actually reachable.
2. 🟠 **N+1 in `POST/PATCH /api/v1/roles`** → batched with `Permission.code.in_()`; role create/update went from 89 → 3 queries.
3. 🟠 **`GET /auth/me` returned 500 on email collision during auto-provision** → now raises `AuthError("auth.email_conflict")` → 401. Regression test added.
4. 🟡 OpenAPI/Postman baseline drift (pagination bounds) → regenerated.
5. 🟡 30 files with non-canonical import order → auto-fixed; `backend/pyproject.toml` now pins ruff `I` + `B` rules.

Verification: ruff + mypy + bandit + pip-audit all clean. Alembic `upgrade → downgrade → upgrade` reversible. Seed idempotent (11 counts match on both runs). Health endpoints 200. OpenAPI drift clean. **120/120 pytest green in ~12 s.**

Known gap deferred to Sprint 1.6 (per PRD): **22 FKs lack supporting indexes** — cardinality is small today; migration `013_indexes.py` will cover them alongside the other performance work already scoped in 1.6.

### P2
- Sprint 1.7 — Ops runbooks (Backup, DR, Migration, Rollback, Restore, Version-Upgrade) + OpenAPI snapshot committed to `/docs/api/openapi.json`.
- Sprint 2+ — Master-data CRUD UI, catalog UI, inventory UI, orders workflow, invoicing, distributor portal, storefront rebuild in React 19.

## Environment
- Local Postgres 15 running on `localhost:5432` (databases: `kaya_bos`, `kaya_bos_test`, user `kaya` / `kaya_dev`).
- Env file: `backend/.env` (contains `DATABASE_URL`, `DATABASE_URL_SYNC`, and `_TEST` variants).
- `backend/server.py` (legacy Mongo MVP) was **deleted** in the Sprint 1.3-stable checkpoint. FastAPI (`app.main:app`) is now the only backend entry point. Legacy React storefront under `frontend/src/**` is still on disk but frozen — see `docs/DEPRECATED.md`.

## Credentials
See `/app/memory/test_credentials.md`.
