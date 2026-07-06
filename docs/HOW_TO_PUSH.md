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

---

## Sprint 1.3 Quality Gate — publish + tag (2026-02-06)

The Quality Gate closed clean (see `docs/sprints/S1.3_QUALITY_GATE.md`,
overall score **9.0 / 10**). Ship it in one push:

### 4. Save the Quality Gate branch
- Click **Save to GitHub**.
- Branch: `sprint/1.3-quality-gate`.
- Commit message: `Sprint 1.3 Quality Gate — supervisor fix, N+1 batching, auth email-collision guard, ruff pyproject`.
- Base for PR: `main`.

### 5. PR body (paste)
> **Sprint 1.3 Quality Gate**
> Overall production-readiness: **9.0 / 10** — zero Critical / High findings open.
>
> **Fixes**
> - 🔴 Supervisor was crash-looping on legacy `backend/server.py` (Mongo MVP, `KeyError: JWT_SECRET`). Repointed `[program:backend]` in `/etc/supervisor/conf.d/supervisord.conf` to `uvicorn app.main:app`. This is a preview-container environment fix; `docker-compose.yml` already targets `app.main:app`.
> - 🟠 N+1 in `POST/PATCH /api/v1/roles` (`admin.py`) — permission lookup batched with `Permission.code.in_()`; role create/update went from 89 → 3 queries.
> - 🟠 `GET /api/v1/auth/me` returned 500 on `uq_users_email` collision during auto-provision (`auth_service.py`). Now raises `AuthError("auth.email_conflict")` → 401 with the unified error envelope. New regression test.
> - 🟡 OpenAPI + Postman baseline regenerated (pagination bounds).
> - 🟡 30 files re-ordered by isort (ruff `--select=I001 --fix`). New `backend/pyproject.toml` pins ruff `E, F, W, I, B` so drift is caught by CI.
>
> **Verification (all green)**
> - ruff `E, F, W, I, B` — clean on `backend/app`, `backend/tests`, `backend/migrations`, `scripts`.
> - mypy-strict — 0 issues in 41 source files.
> - bandit — 0 findings, 3 238 LOC.
> - pip-audit — 0 CVEs.
> - pytest — **120 passed in ~12 s** (2 xdist workers, `loadscope`).
> - alembic `upgrade head → downgrade base → upgrade head` reversible; ends at `005`.
> - alembic check — 0 drift.
> - Seed idempotent (identical counts across two runs).
> - OpenAPI / Postman drift — clean.
> - Health endpoints — `/live` `/ready` `/db` all 200.
> - Frontend — serves 200 on 3000.
>
> **Deliverables**
> - `docs/sprints/S1.3_QUALITY_GATE.md` — full 10-section report.
> - `CHANGELOG.md` — Quality Gate entry.
> - `backend/pyproject.toml` — new.
> - `backend/tests/test_auth.py::test_email_collision_on_autoprovision_returns_401` — new regression test.
> - `docs/api/openapi.{json,yaml}` + `docs/api/postman_collection.json` — refreshed.
> - `test_reports/iteration_{1,2}.json` — testing-agent evidence.
>
> **Known gap (deferred to Sprint 1.6 per PRD roadmap)**
> - 22 FK columns lack supporting B-tree indexes (cardinality small today; will land as migration `013_indexes.py` alongside triggers/views work already scoped in 1.6).

### 6. Tag the merge
After the PR merges into `main`, add a lightweight tag via the GitHub UI:
- Releases → **Draft a new release** → Tag `sprint-1.3-quality-gate` → target `main` → paste the PR body as the release notes.

### 7. Fresh-clone smoke test (optional but recommended)
```bash
git clone https://github.com/ashokchauhansmailbox/kayas-herbals-erp
cd kayas-herbals-erp
docker compose up --build       # migrations + seed + api on :8001, postgres on :5432
curl localhost:8001/api/v1/health/db
cd frontend && yarn && yarn start   # storefront on :3000
```
