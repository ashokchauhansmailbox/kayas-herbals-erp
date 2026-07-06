# Technical debt register

_Single source of truth for every deferred item across Kaya BOS sprints._

Every row below is either **rejected** (with reason) or **scheduled** (with the sprint
that will resolve it). Nothing lives here on memory alone. When an item is closed, move
its row to the "Resolved" section at the bottom of the file with the sprint tag that
resolved it.

## Priority scale

| Priority | Meaning |
|---|---|
| **High** | Blocks a future sprint or presents real production risk. Must be resolved in the sprint listed below or earlier. |
| **Medium** | Improves architecture/perf/DX materially but no downstream code depends on it. |
| **Low** | Nice-to-have polish. May be batched into a housekeeping PR. |

## Open items

| ID | Description | Reason deferred | Priority | Planned sprint | Status |
|---|---|---|---|---|---|
| TD-01 | **22 FK columns lack supporting B-tree indexes.** Includes `role_permissions(permission_id)`, `user_roles(role_id)`, `stock_ledger(warehouse_id)`, `stock_snapshots(warehouse_id)`, `stock_alerts(batch_id)`, `stock_snapshots(batch_id)`, `stock_transfer_items(batch_id)`, `stock_transfer_items(variant_id)`, `products(hsn_code_id)`, `products(default_unit_id)`, `product_variants(unit_id)`, `hsn_codes(default_gst_rate_id)`, `units(base_unit_id)`, `user_invitations(role_id)`, plus several `_by` actor FKs. | PRD scoped "performance indexes + triggers + views" as **Sprint 1.6** work. Cardinality on these tables is small today (89 permissions × 9 roles, single warehouse); sequential scans stay sub-millisecond. Adding indexes now would spread the change across three sprints instead of one clean migration. | Medium | 1.6 | Open |
| TD-02 | **Legacy React storefront under `frontend/src/**` is frozen.** 15 `useEffect` / `useCallback` dependency warnings, 6 components > 100 LOC, 7 array-index React keys, `localStorage`-backed JWT + cart storage, one empty catch block, inline `value` props on context providers. **Additionally 18 ESLint errors surfaced 2026-02-06:** 15 × `react/no-unescaped-entities` (apostrophes/quotes in JSX text — cosmetic, no runtime impact), 1 × `no-empty` in `AuthContext.jsx:41` catch block (guarding a call to `/api/auth/logout` — an endpoint that does not exist on FastAPI, so the block is unreachable), 2 × `react/no-unstable-nested-components` in vendored `components/ui/calendar.jsx` (shadcn/ui copy-in; the Calendar isn't wired into any current route), 1 × `react/no-unknown-property` for `cmdk-input-wrapper` on `components/ui/command.jsx:36` (attribute read by the `cmdk` library — false positive from `no-unknown-property`). None are security or runtime bugs. | Whole folder is scheduled for wholesale replacement in Sprint 2 (React 19 + Vite + TypeScript + Tailwind + shadcn/ui + TanStack Query + Zustand + Zod). Fixes to this code are throwaway. `localStorage` JWT risk is **unreachable today** — the frontend targets `/api/auth/*` (no `/v1`) which does not exist on the FastAPI backend, so no token is ever stored. See `docs/DEPRECATED.md`. | Low | 2.0 | Open (frozen) |
| TD-03 | **Rate limiting on `/api/v1/auth/*`.** No brute-force throttling in front of JWT verify. | Preview environment only; production hardening scoped to Sprint 1.5 alongside Payments. Redis-token-bucket middleware selected in `docs/architecture/06-non-functional.md`. | High | 1.5 | Open |
| TD-04 | **Supabase RLS policies not yet enabled.** Defence-in-depth if the API is bypassed. | Requires a real Supabase project; policies are drafted in `docs/architecture/04-rls-policies.md` and will land alongside the staging environment in Sprint 1.6. | High | 1.6 | Open |
| TD-05 | **`SUPABASE_JWT_SECRET` in `backend/.env` is the dev placeholder** (`dev-only-supabase-jwt-secret-change-me-32chars`). | Preview only; rotation is a human step before staging deploy. Tracked in Ops checklist. | High | 1.6 (staging) | Open (human step) |
| TD-06 | **Ops runbooks: Backup, DR, Rollback.** | Scoped to Sprint 1.7 (Release readiness). | Medium | 1.7 | Open |
| TD-07 | **Final OpenAPI snapshot + release readiness review.** | Sprint 1.7 by design. | Medium | 1.7 | Open |
| TD-08 | **Legacy `backend/server.py` — DELETED in `sprint-1.3-stable`.** | — | — | — | Resolved 2026-02-06 |

## Rejected findings (documented for auditability)

Everything below has been formally reviewed and refused. Do not re-open without new evidence.

| ID | Finding | Refusal reason |
|---|---|---|
| REJ-01 | "Replace `is None` with `== None` (56 instances)." | PEP 8 §Programming Recommendations mandates `is` / `is not` for singleton comparisons. Ruff, MyPy-strict, and Bandit all accept the current code. Applying this change would introduce a regression against a language standard. |
| REJ-02 | "3 possibly undefined Python variables." | Traced to two pyflakes false positives: (a) `# noqa: F401` module-level re-exports in `app/models/__init__.py` required for Alembic autogenerate to discover mapped classes; (b) forward-reference string annotation in `tests/conftest.py:130` already carrying `# noqa: F821`. Ruff strict mode passes. |
| REJ-03 | "Split Alembic migrations 002-005 `upgrade()` blocks into logical sections." | `op.create_table(...)` sequences must stay atomic to preserve reversibility. Splitting them fragments the up/down pair and would fail the CI cycle test. Standard Alembic idiom. |
| REJ-04 | "`_build_order_from_input()` in `server.py` has cyclomatic complexity 11." | `server.py` was deleted in `sprint-1.3-stable`. |

## Resolved

| ID | Description | Resolved sprint |
|---|---|---|
| TD-08 | Delete `backend/server.py` (legacy Mongo MVP, 564 LOC). | 1.3-stable (2026-02-06) |
| — | Supervisor was pointing at `server:app` — fixed to `app.main:app`. | 1.3 Quality Gate (2026-02-06) |
| — | N+1 in `POST/PATCH /api/v1/roles` (per-permission lookup). | 1.3 Quality Gate (2026-02-06) |
| — | `GET /api/v1/auth/me` returned 500 on email collision during auto-provision. | 1.3 Quality Gate (2026-02-06) |
| — | OpenAPI + Postman baseline drift on pagination bounds. | 1.3 Quality Gate (2026-02-06) |
| — | 30 files with non-canonical import order. | 1.3 Quality Gate (2026-02-06) |
| — | Unused `tenacity` dependency in `backend/requirements.txt`. | 1.3-stable (2026-02-06) |
| — | Untracked `frontend/yarn.lock` — added, deterministic fresh-clone builds. | 1.3-stable (2026-02-06) |
| — | Cyclomatic complexity of `admin.update_role` and `_seed_roles` (extracted helpers). | 1.3-stable (2026-02-06) |
| — | Hard-coded test-secret literal in `tests/test_auth.py`. | 1.3-stable (2026-02-06) |
