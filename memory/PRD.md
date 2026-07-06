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
- Smoke tests: 32 model-contract cases + 5 migration-cycle cases, **39/39 green**.
- Fixed pre-existing broken import in `app/api/v1/__init__.py` (was importing non-existent routes).

Round-trip verified: `alembic upgrade head → downgrade base → upgrade head`. `alembic check` reports zero drift.

## Backlog

### P0 — next up
- **Sprint 1.2 — Catalog + Inventory**: `catalog.py` (products, variants, images, certifications, price histories) + `inventory.py` (batches, stock ledger + snapshots, transfers, alerts). Migrations `004`, `005`.

### P1
- Sprint 1.3 — Purchase + Distributor + Customer models · migrations `006`, `007`.
- Sprint 1.4 — Orders + Billing + Payments · migrations `008`, `009`.
- Sprint 1.5 — Marketing + Support + Settings + indexes/views/triggers · migrations `010`, `011`, `012`.
- Sprint 1.6 — Supabase JWT verifier + capability RBAC middleware + seeds (permissions/roles/master data) + Pydantic schemas + route stubs.

### P2
- Sprint 1.7 — Ops runbooks (Backup, DR, Migration, Rollback, Restore, Version-Upgrade) + OpenAPI snapshot committed to `/docs/api/openapi.json`.
- Sprint 2+ — Master-data CRUD UI, catalog UI, inventory UI, orders workflow, invoicing, distributor portal, storefront rebuild in React 19.

## Environment
- Local Postgres 15 running on `localhost:5432` (databases: `kaya_bos`, `kaya_bos_test`, user `kaya` / `kaya_dev`).
- Env file: `backend/.env` (contains `DATABASE_URL`, `DATABASE_URL_SYNC`, and `_TEST` variants).
- The legacy MongoDB MVP (`backend/server.py`) is still on disk but no longer wired to the FastAPI app — kept until Sprint 2 UI parity.

## Credentials
See `/app/memory/test_credentials.md`.
