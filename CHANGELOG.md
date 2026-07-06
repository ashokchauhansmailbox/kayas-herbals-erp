# Changelog

All notable changes to the Kaya BOS backend/frontend are logged here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: sprint-based, not SemVer.

## [Unreleased]

## Sprint 1.1 — Database Foundation — 2026-02-06

### Added
- SQLAlchemy declarative `Base` with unified naming convention (`app/db/base.py`).
- Async engine + session factory + `configure_engine()` test hook (`app/db/session.py`).
- Reusable column mixins: `TimestampMixin`, `ActorMixin`, `SoftDeleteMixin`, `VersionMixin` (`app/db/mixins.py`).
- Shared Postgres type helpers: `uuid_pk()`, `jsonb_column()` (`app/db/types.py`).
- Identity models: `User`, `Role`, `Permission`, `RolePermission`, `UserRole`, `Session`, `UserInvitation`, `AuditLog`, `ActivityLog`.
- Master-data models: `Unit`, `GstRate`, `HsnCode`, `Category`, `Brand`, `Warehouse`, `PaymentTerm`, `TaxRule`, `Transporter`, `CourierPartner`.
- Alembic setup: `alembic.ini`, `migrations/env.py` (async-aware + `-x db_url=` override), `migrations/script.py.mako`.
- Migration `001` — pgcrypto/uuid-ossp/citext/pg_trgm extensions + 9 native enum types.
- Migration `002` — identity core (9 tables) with immutable audit_logs shape.
- Migration `003` — master-data (10 tables) with actor-column FKs added post-create to break the circular dep with `users`.
- Per-migration docs under `/docs/database/`.
- Health endpoints: `/api/v1/health/live`, `/ready`, `/db`.
- Smoke tests (39 cases) covering model contracts + migration cycle + drift check.

### Fixed
- `app/api/v1/__init__.py` was importing route modules that did not exist yet, preventing FastAPI startup. Router now only wires the health module; other modules will be added by their owning sub-sprints.
- `app/core/logging.py` E401 lint violation (multiple imports on one line).

### Sprint plan
Sprint 1 has been split into sub-sprints. See `/docs/sprints/S1.1.md` for the mapping of remaining items (catalog + inventory → 1.2, purchase/distributor/customer → 1.3, orders/billing → 1.4, marketing/support/settings → 1.5, RBAC + seeds + routes → 1.6, ops runbooks → 1.7).

## Sprint 1 (scaffolding-only) — 2026-01

### Added
- `docker-compose.yml` — Postgres 16 + Redis 7 + backend.
- `backend/Dockerfile`, `requirements.txt`, `.env.example`.
- `backend/app/core/` — `Settings` (pydantic-settings), structlog logging, unified error envelope.
- `backend/app/main.py` — FastAPI app, CORS, `/api/v1` mount, OpenAPI at `/api/v1/docs`, top-level `/health`.

## Sprint 0 — 2026-01

### Added
- Monorepo skeleton (`backend/`, `frontend/`, `packages/`, `docs/`).
- Brand-token package (`packages/ui/theme.ts`).
- Decisions frozen (`docs/DECISIONS.md`).
- Architecture docs `01`–`08`.
