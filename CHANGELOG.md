# Changelog

All notable changes to the Kaya BOS backend/frontend are logged here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: sprint-based, not SemVer.

## [Unreleased]

## Sprint 1.3 Stable (checkpoint tag `sprint-1.3-stable`) — 2026-02-06

### Removed
- 🗑 **Deleted `backend/server.py`** (564 LOC, legacy MongoDB MVP). Zero live references remained: supervisor already ran `app.main:app`, `docker-compose.yml` already targeted `app.main:app`, CI ran the FastAPI pipeline only. `requirements.txt` never listed the MVP-only deps (`motor`, `bcrypt`), so nothing to prune there.
- 🗑 **Dropped `tenacity==9.0.0`** from `backend/requirements.txt` — zero direct imports across `app/`, `tests/`, `migrations/`, and `scripts/`. Confirmed transitive availability via `emergentintegrations → google-genai` if a future sprint needs it, but Sprint 1.3 does not.
- FastAPI (`app.main:app`) is now the **only** supported backend entry point.

### Added
- `docs/DEPRECATED.md` — catalogues the frozen legacy React storefront under `frontend/src/**` (why it's still on disk, which files are legacy, known findings from the 2026-02-06 external code review, and the Sprint-2 rebuild plan that replaces the entire folder). Includes the security-reachability analysis: the legacy frontend's auth flow points at `/api/auth/*` (no `/v1`) which does not exist on FastAPI, so the flagged `localStorage`-JWT XSS risk is **unreachable in the current preview** — no exploit path terminates in a live effect.
- **`README.md`** — full 13-section onboarding guide replacing the 29-byte stub (project overview, architecture, folder structure, tech stack, local + Docker setup, env vars, migrations, tests, code-quality tools, branch strategy, sprint workflow, deployment).
- **`docs/TECHNICAL_DEBT.md`** — single source of truth for every deferred item with description, reason, priority, planned sprint, and status. Includes a "Rejected findings" section documenting refusals with citations.
- **`docs/RELEASE_MANIFEST.md`** — per-checkpoint manifest for `sprint-1.3-stable` capturing commit/branch/tag, migration head, schema version, API + OpenAPI + Postman versions, dep pins, Docker base images, verification gates, known issues, and the exact rollback procedure. Includes a template block for future stable tags.

### Refactored (Sprint 1.3 code we own — no behaviour change)
- `app/api/v1/routes/admin.py` — extracted `_assign_role_permissions` helper shared by `create_role` and `update_role`. Cyclomatic complexity of `update_role` down from 11 to ~4.
- `app/seeds/run.py` — extracted `_role_from_spec`, `_validate_perm_codes`, `_remap_role_perms` helpers. Complexity of `_seed_roles` down from 13 to ~5. Idempotency verified with two consecutive runs producing identical counts.
- `tests/test_auth.py::test_wrong_signing_secret_rejected` — hardcoded 32-byte secret literal replaced by an env-var-driven constant (`TEST_WRONG_JWT_SECRET`) with a computed fallback.

### Rejected findings (documented for auditability)
- **"`is None` → `== None`"** — refused. PEP 8 mandates `is`/`is not` for singleton comparisons. Ruff, MyPy-strict, and Bandit accept this pattern. The 15 existing usages in `auth_service.py`, `audit_service.py`, and `seeds/run.py` are all correct.
- **"3 possibly undefined Python variables"** — traced to pyflakes false positives on `# noqa: F401` module-level re-exports required by Alembic autogenerate and one `# noqa: F821` forward-ref string annotation in `tests/conftest.py`. Ruff and MyPy strict both pass.
- **"Migrations 002-005 have long `upgrade()` blocks"** — refused. `op.create_table(...)` sequences must stay atomic to keep `upgrade`/`downgrade` reversible. Standard Alembic idiom.
- **Legacy frontend refactoring (15 useEffect deps, 6 oversized components, array-index keys, localStorage tokens)** — deferred to the Sprint 2 rebuild per `docs/DEPRECATED.md`. No reachable exploit path today.

### Verification (all green)
- ruff `E, F, W, I, B` — 0 issues.
- MyPy-strict — 0 issues in 41 files.
- Bandit — 0 findings.
- pip-audit — 0 CVEs.
- pytest — **120 passed** in ~12 s.
- alembic upgrade → downgrade → upgrade reversible; ends at `005`.
- alembic check — 0 drift.
- Seed idempotent (identical counts across two runs post-refactor).
- OpenAPI + Postman drift — clean.

## Sprint 1.3 Quality Gate — 2026-02-06

### Fixed
- 🔴 **Supervisor was booting `backend/server.py` (legacy Mongo MVP)** — the container reported RUNNING but was crash-looping on `KeyError: 'JWT_SECRET'`, so the new `app.main:app` had never actually served a request through supervisor. Repointed `[program:backend]` in `/etc/supervisor/conf.d/supervisord.conf` to `uvicorn app.main:app`; verified `/api/v1/health/{live,ready,db}` all return 200.
- 🟠 **N+1 query in `POST/PATCH /api/v1/roles`** — the create/update handlers looped one `SELECT permissions WHERE code = ?` per requested code (up to 89 for `super_admin`). Batched into a single `Permission.code.in_()` fetch + dict lookup. Now O(3) queries flat. `admin.py`.
- 🟠 **`GET /api/v1/auth/me` returned 500 on email collision during auto-provision** — a JWT with a new `sub` UUID but a pre-existing email raised a raw `IntegrityError` on `uq_users_email`. Now pre-checks by email and raises `AuthError("auth.email_conflict")` → HTTP 401 with the unified error envelope. `auth_service.py`. New regression test.
- 🟡 **OpenAPI/Postman baseline drift** — pagination bounds (`minimum: 1`, `maximum: 200` on `page`/`page_size`) added earlier were never regenerated. `docs/api/openapi.{json,yaml}` and `postman_collection.json` refreshed.
- 🟡 **30 files with non-canonical import order** — auto-fixed. `backend/pyproject.toml` added to pin ruff rule set (`E, F, W, I, B`) so the existing CI `ruff check` step now enforces isort ordering going forward.

### Added
- `docs/sprints/S1.3_QUALITY_GATE.md` — full technical debt, security, and performance report with dimension scores (Overall production-readiness: **9.0 / 10**).
- `backend/tests/test_auth.py::test_email_collision_on_autoprovision_returns_401` — regression test for the auto-provision fix.
- `backend/pyproject.toml` — ruff config.

### Verified
- Ruff / MyPy-strict / Bandit / pip-audit: clean.
- Alembic `upgrade head → downgrade base → upgrade head` reversible on a scratch database.
- Seed script idempotent (identical counts across two invocations).
- OpenAPI + Postman drift: none.
- Pytest: **120 passed in ~12 s** (119 pre-existing + 1 new regression).
- Testing agent verified iteration_1 (all 8 gates green) and iteration_2 (email-collision fix green).

### Deferred (planned, not blocking)
- Migration `013_indexes.py` to add covering B-tree indexes on 22 FKs (`role_permissions.permission_id`, `user_roles.role_id`, `stock_ledger.warehouse_id`, `stock_snapshots.warehouse_id`, batch/variant/hsn/unit FKs on catalog & inventory). Scoped in Sprint 1.6 per PRD.
- Delete `backend/server.py` (legacy Mongo MVP) during Sprint 2 UI cutover.

## Sprint 1.3 — Auth + RBAC + Audit + Seeds + Route Foundations — 2026-02-06

### Added
- **Security core**: `app/core/security.py` — HS256 JWT verification against `SUPABASE_JWT_SECRET` (validates signature, aud, exp, sub). Also exposes `mint_token()` for pytest.
- **Dependencies**: `app/deps.py` — `get_db`, `get_token_claims`, `get_current_user`, `require("perm.code")`, `request_id`.
- **Auth service**: `app/services/auth_service.py` — resolves the local user, auto-provisions on first login, honours suspension/deletion, records `sessions.jti` and honours `revoked_at`.
- **Audit framework**: `app/services/audit_service.py` — `AuditContext(before/after → deepdiff)` writes to `audit_logs` in the same tx as the mutation; `log_activity()` for the read-side event stream.
- **Seed data**:
  - 89-entry permission catalogue (`app/seeds/permissions.py`).
  - 9 system roles + full role→permission mapping (`app/seeds/roles.py`).
  - Master data: 8 units, 5 GST rates, 12 HSN codes (herbal/ayurvedic), 6 categories, 1 brand (Kaya's Herbals), 1 warehouse (KH-BLR-MAIN), 5 payment terms, 4 tax rules, 5 courier partners.
  - Idempotent runner `python -m app.seeds.run` — re-runs are safe and re-sync system-role permission mapping.
- **Pydantic schemas**: `app/schemas/common.py`, `auth.py`, `admin.py`.
- **API routes** (18 endpoints under `/api/v1`):
  - `/auth/me`, `/auth/sessions`, `/auth/logout`
  - `/users` list/get/patch/assign-role/revoke-role
  - `/roles` list/get/create/update/delete (system-role protection)
  - `/permissions` list + filter by module
  - `/invitations` list/create/revoke
  - `/audit/logs`, `/audit/activity` paginated
- **Postman collection baseline** (`docs/api/postman_collection.json`) — 23 requests, 7 folders, generated deterministically from the OpenAPI spec via `scripts/generate_postman.py`.
- **Contract drift check** upgraded to cover openapi.json + openapi.yaml + postman_collection.json.
- **Tests** — 30 new cases (11 auth, 9 RBAC, 10 audit + OWASP incl. `alg=none` rejection, IDOR, SQL-injection input safety, missing-bearer / missing-permission / no-internals-leak).
- CI: new `seed-idempotency` and `docker-compose-boot` gates; contract check now enforces all three baseline files.

### Changed
- `pytest.ini` — pinned `asyncio_default_fixture_loop_scope = session` and `asyncio_default_test_loop_scope = session` (requires pytest-asyncio ≥ 1.4).
- `requirements.txt` — pytest 8.4, pytest-asyncio 1.4, httpx pinned.
- `docker-compose.yml` — backend now runs `alembic upgrade head && python -m app.seeds.run` before uvicorn.

### Roadmap adjustment
Sprint 1.3 was originally planned as "Purchase + Distributor + Customer" but was swapped forward with the Auth/RBAC track so subsequent sprints have real identity from day one. Purchase/Distributor/Customer moved to Sprint 1.4.

## Sprint 1.2 — Catalog + Inventory — 2026-02-06

### Added
- **Catalog models** (`app/models/catalog.py`): `Product`, `ProductVariant`, `ProductImage`, `ProductDocument`, `Certification`, `ProductPriceHistory`, `PurchasePriceHistory`.
- **Inventory models** (`app/models/inventory.py`): `Batch`, `StockAdjustment`, `StockTransfer`, `StockTransferItem`, `StockLedger`, `StockSnapshot`, `StockAlert`.
- Migration `004` — catalog: 7 tables with product↔category/brand/hsn/unit FKs and append-only journals for selling + purchase price history. `purchase_price_history.vendor_id/po_id` intentionally left FK-less (Sprint 1.3 adds them).
- Migration `005` — inventory: 7 tables + `v_stock_valuation` view (qty × cost_per_unit + days_to_expiry). CHECK constraints enforce BR-INV-02, BR-INV-08, positive transfer qty, and distinct transfer warehouses. Functional unique index on `stock_snapshots` uses COALESCE so NULL `batch_id` still deduplicates.
- Per-migration docs (`docs/database/004-catalog.md`, `005-inventory.md`) and Sprint 1.2 summary (`docs/sprints/S1.2.md`).
- Integration + smoke tests (`tests/test_catalog_inventory.py`) covering catalog CRUD, journal append shape, CHECK-constraint enforcement, valuation view correctness, and stock alert lifecycle.
- Per-worker test databases in `conftest.py` so pytest-xdist workers no longer collide when running the migration cycle + integration suites in parallel.

### Changed
- `app/models/__init__.py` — extended re-exports for catalog + inventory models.
- `tests/test_models_schema.py` — table set expanded, added Sprint 1.2 shape assertions (unique-constraint pairs, CHECK constraint presence, price-journal append-only shape).
- `tests/test_migrations_cycle.py` — asserts `v_stock_valuation` view exists after upgrade.

## Sprint 1.1.1 — Pre-Sprint-1.2 tooling — 2026-02-06

### Added
- OpenAPI baseline: `docs/api/openapi.json` + `docs/api/openapi.yaml` (generated deterministically from `app.main.app.openapi()`).
- `scripts/generate_openapi.py`, `scripts/check_openapi_drift.py`.
- `.github/workflows/ci.yml` — CI pipeline: ruff → mypy → pytest → alembic up/down/up + alembic check → OpenAPI drift check.
- `backend/.env.example`, `backend/mypy.ini`.
- `infra/postgres-init/01-create-test-db.sql` — bootstraps `kaya_bos_test` inside the docker compose Postgres image.

### Changed
- `docker-compose.yml` — no longer references the not-yet-existing seed script; only runs `alembic upgrade head` before uvicorn.

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
