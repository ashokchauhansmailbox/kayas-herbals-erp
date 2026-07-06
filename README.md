# Kaya BOS — Business Operating System

> Production-grade ERP + Inventory + Billing + Distributor + E-commerce platform for
> **Kaya's Herbals**. FastAPI backend, PostgreSQL data plane, React storefront +
> admin dashboard, containerized via Docker Compose, delivered sprint-by-sprint.

**Current milestone:** `sprint-1.3-stable` (2026-02-06) — Identity Core complete.
**Test suite:** 120 backend tests, 100 % passing. **Alembic head:** `005`. **Tables:** 34.
**OpenAPI operations:** 23. **Overall quality score:** 9.0 / 10 (see `docs/sprints/S1.3_QUALITY_GATE.md`).

---

## Table of contents

1. [Project overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Folder structure](#3-folder-structure)
4. [Technology stack](#4-technology-stack)
5. [Local development](#5-local-development)
6. [Docker setup](#6-docker-setup)
7. [Environment variables](#7-environment-variables)
8. [Database migrations](#8-database-migrations)
9. [Running tests](#9-running-tests)
10. [Code quality tools](#10-code-quality-tools)
11. [Branch strategy](#11-branch-strategy)
12. [Sprint workflow](#12-sprint-workflow)
13. [Deployment overview](#13-deployment-overview)

---

## 1. Project overview

Kaya BOS is the single system of record that runs everything Kaya's Herbals does after
"we have a product to sell":

| Module | Sprint | Status |
|---|---|---|
| Identity + RBAC + Audit | 1.3 | ✅ Stable |
| Catalog + Inventory | 1.2 | ✅ Stable |
| Purchase + Distributor + Customer | 1.4 | ✅ Stable (2026-02-06) |
| Orders + Billing + Payments | 1.5 | ⏳ Next |
| Marketing + Support + Settings + Perf indexes | 1.6 | Planned |
| Ops runbooks + DR + release readiness | 1.7 | Planned |
| React 19 rebuild (storefront + admin) | 2.x | Planned |

Every sprint delivers reversible migrations, comprehensive tests, and updated OpenAPI +
Postman baselines. Nothing merges to `main` without passing the full CI matrix.

## 2. Architecture

Clean Architecture inside a modular monolith.

```
┌───────────────────────────────────────────────────────────────┐
│                     HTTP  (FastAPI, /api/v1/*)                │
└───────────────────────────────────────────────────────────────┘
      │                     │                       │
      ▼                     ▼                       ▼
  Route layer          Route layer            Route layer
  (auth.py …)          (users.py …)           (admin.py …)
      │                     │                       │
      └─────────────► Services ◄────────────────────┘
                      (auth_service, audit_service)
                            │
                            ▼
                    SQLAlchemy 2.0 async
                       (models/*.py)
                            │
                            ▼
                       PostgreSQL 15
                     (34 tables, 001-005)
```

**Rules the layout enforces:**
- Routes call services, never each other.
- Services call models, never routes.
- Models never import services or routes.
- Seeds only import models (never routes or services).
- Every mutating route is guarded by `Depends(require("perm.code"))`.
- Every state change is wrapped in `AuditContext(...)` (before / after JSONB + deepdiff).
- All I/O is async. No `sqlalchemy.orm.Session` anywhere.

**Reference documents:**
- [`docs/architecture/`](docs/architecture/) — 8 numbered ADR-style notes.
- [`docs/database/`](docs/database/) — one file per migration (001 → 005).
- [`docs/sprints/`](docs/sprints/) — sprint plans + quality gates.
- [`docs/api/`](docs/api/) — versioned `openapi.{json,yaml}` + Postman collection.

## 3. Folder structure

```
kayas-herbals-erp/
├── backend/
│   ├── app/                     # FastAPI application (main.py = entry point)
│   │   ├── api/v1/routes/       # HTTP handlers per resource
│   │   ├── core/                # config, security, errors
│   │   ├── db/                  # base, session, mixins
│   │   ├── models/              # SQLAlchemy 2.0 mapped classes
│   │   ├── schemas/             # Pydantic v2 IO models
│   │   ├── seeds/               # idempotent seed data (89 perms, 9 roles, …)
│   │   └── services/            # domain services (auth, audit)
│   ├── migrations/versions/     # Alembic revisions 001 → head
│   ├── tests/                   # pytest-asyncio + xdist (120 tests, ~12 s)
│   ├── alembic.ini
│   ├── mypy.ini
│   ├── pyproject.toml           # ruff config
│   └── requirements.txt
├── frontend/                    # React storefront (LEGACY — see docs/DEPRECATED.md)
├── docs/
│   ├── api/                     # OpenAPI + Postman baselines
│   ├── architecture/            # ADRs
│   ├── database/                # per-migration notes
│   ├── sprints/                 # sprint plans + quality gates
│   ├── DEPRECATED.md
│   ├── HOW_TO_PUSH.md
│   ├── TECHNICAL_DEBT.md
│   └── RELEASE_MANIFEST.md
├── scripts/                     # generate/verify OpenAPI + Postman
├── .github/workflows/           # CI matrix
├── docker-compose.yml
├── CHANGELOG.md
└── README.md
```

## 4. Technology stack

**Backend**
- Python 3.11
- FastAPI 0.139 · Starlette 1.3
- Pydantic v2 (`pydantic 2.10`, `pydantic-settings 2.6`)
- SQLAlchemy 2.0 async · asyncpg 0.30 · Alembic 1.14
- pyjwt (Supabase HS256), structlog, deepdiff
- pytest 9 · pytest-asyncio 1.4 · pytest-xdist 3.6

**Frontend (frozen legacy — will be rebuilt in Sprint 2)**
- React 19 · CRA · Tailwind · shadcn/ui
- axios · react-router 6

**Data plane**
- PostgreSQL 15 with `citext`, `pg_trgm`, `pgcrypto`, `uuid-ossp`
- Enum-backed status columns, `CHECK` constraints, deferred FKs where needed

**Tooling & CI**
- Ruff (E, F, W, I, B) · MyPy-strict · Bandit · pip-audit
- Docker Compose (dev, CI smoke)
- GitHub Actions matrix: lint → type-check → security scan → pytest → Alembic cycle → seed idempotency → OpenAPI drift → compose smoke

## 5. Local development

Prerequisites: Python 3.11, PostgreSQL 15, Node ≥ 20, Yarn.

```bash
git clone https://github.com/<org>/kayas-herbals-erp
cd kayas-herbals-erp

# --- backend ---
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # fill in DATABASE_URL, SUPABASE_JWT_SECRET, …
alembic upgrade head
python -m app.seeds.run
uvicorn app.main:app --reload --port 8001
# → http://localhost:8001/api/v1/docs

# --- frontend (legacy) ---
cd ../frontend
yarn install
yarn start
# → http://localhost:3000
```

## 6. Docker setup

```bash
docker compose up --build
```

This spins up:
- `postgres` on `:5432`
- `backend` on `:8001` (auto-runs `alembic upgrade head` and `python -m app.seeds.run` on boot)
- `frontend` on `:3000`

Health check: `curl http://localhost:8001/api/v1/health/db` → `{"alembic_revision":"005", ...}`.

Tear down (preserve data): `docker compose down`.
Tear down (nuke data): `docker compose down -v`.

## 7. Environment variables

Copy `backend/.env.example` → `backend/.env` and fill in:

| Variable | Purpose | Default (dev) |
|---|---|---|
| `DATABASE_URL` | async SQLAlchemy URL | `postgresql+asyncpg://kaya:kaya_dev@localhost:5432/kaya_bos` |
| `DATABASE_URL_SYNC` | Alembic sync URL | `postgresql+psycopg2://kaya:kaya_dev@localhost:5432/kaya_bos` |
| `DATABASE_URL_TEST` | async test DB URL | `postgresql+asyncpg://kaya:kaya_dev@localhost:5432/kaya_bos_test` |
| `DATABASE_URL_TEST_SYNC` | sync test DB URL | (same, psycopg2) |
| `SUPABASE_JWT_SECRET` | HS256 verifier | `dev-only-…-change-me-32chars` |
| `SUPABASE_JWT_ISSUER` | expected `iss` claim | `kaya-bos-dev` |
| `SUPABASE_JWT_AUDIENCE` | expected `aud` claim | `kaya-bos-clients` |
| `APP_ENV` | `dev` / `staging` / `production` | `dev` |
| `CORS_ORIGINS` | CSV of allowed origins | `http://localhost:3000` |

**Never commit real secrets.** `.env` is gitignored.

## 8. Database migrations

```bash
# apply
alembic upgrade head

# roll back one step
alembic downgrade -1

# roll back everything
alembic downgrade base

# create a new revision (Sprint 1.4+)
alembic revision -m "006 — purchase" --rev-id 006
```

Every migration ships with a matching `docs/database/00N-<slug>.md` describing intent,
tables added, constraints, and rollback behaviour.

**Reversibility is a hard requirement.** CI runs `upgrade head → downgrade base → upgrade head`
on every PR.

## 9. Running tests

```bash
cd backend
python -m pytest              # full suite, ~12 s under xdist
python -m pytest -k rbac      # substring filter
python -m pytest -x --lf      # stop at first fail, re-run last failed
```

Additional gates run in CI (see §10). To reproduce locally:

```bash
ruff check app/ tests/
mypy app/
bandit -r app/
pip-audit -r requirements.txt
python scripts/check_openapi_drift.py   # from repo root
```

## 10. Code quality tools

| Tool | Config | What it enforces |
|---|---|---|
| Ruff | `backend/pyproject.toml` | `E, F, W, I, B` — style + isort + likely bugs |
| MyPy | `backend/mypy.ini` | strict types on `app/`, relaxed on `tests/` and `migrations/` |
| Bandit | defaults | common Python security anti-patterns |
| pip-audit | latest CVE feed | known vulnerabilities in transitive deps |
| pytest | `backend/pytest.ini` | 120 tests, xdist parallel, `loadscope` isolation per DB |
| OpenAPI drift | `scripts/check_openapi_drift.py` | prevents route changes without regenerating `docs/api/openapi.{json,yaml}` |

All six run in the GitHub Actions matrix on every push and PR.

## 11. Branch strategy

- `main` — always green, always deployable.
- `sprint/N.M` — one branch per sprint (e.g. `sprint/1.4-purchase-distributor-customer`).
- `sprint/N.M-<focus>` — sub-branches for major deliverables inside a sprint.
- Merges are squash-only with a Conventional-Commit style subject.
- Tags at every stable checkpoint (`sprint-1.3-stable`, `sprint-1.4-stable`, …).
- Long-lived branches (>1 sprint) are prohibited; if scope grows, split it.

## 12. Sprint workflow

1. **Kick-off:** update `docs/sprints/S<N>.md` with scope, migrations, routes, tests.
2. **Implement:** small logical commits. Every commit builds and passes local tests.
3. **Document:** update `docs/database/*` for schema, `docs/api/*` for routes, `CHANGELOG.md`
   for changes.
4. **Quality gate:** run the full verification suite (§9 + §10). If any gate fails, the
   sprint is not done.
5. **Sprint doc:** produce a summary + score in `docs/sprints/S<N>.md` and a
   `docs/sprints/S<N>_QUALITY_GATE.md` for stable checkpoints.
6. **Release manifest:** append the tag's row to `docs/RELEASE_MANIFEST.md`
   (commit hash, migration head, test count, dep versions, known issues, rollback).
7. **Tag & push:** open a PR into `main`, wait for green CI, squash-merge, tag.
8. **Retrospective:** review deferred debt in `docs/TECHNICAL_DEBT.md` and re-prioritise.

## 13. Deployment overview

- **Preview:** container hosted at `${REACT_APP_BACKEND_URL}`; updated on every push to
  the active sprint branch. Powered by supervisord running `uvicorn app.main:app`.
- **Staging:** planned for Sprint 1.6 (per PRD Ops track). Managed Postgres, secrets in a
  vault, RLS enabled, real Supabase project.
- **Production:** planned for Sprint 1.7. Blue-green rollout via Docker Compose profile
  swap, DB migrations gated behind `alembic upgrade head --sql` review.

Rollback procedure at every checkpoint is captured in `docs/RELEASE_MANIFEST.md` (§Rollback).

---

**Questions?** Start with `docs/architecture/00-overview.md`, then the sprint doc for the
feature you're touching. If something in this README goes stale, it's a bug — please open
an issue titled `docs: readme drift — <what>`.
