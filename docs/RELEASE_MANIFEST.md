# Release manifest

_Single canonical record of every stable checkpoint. Append one row per tag._

Each entry captures exactly enough information to reproduce, verify, and — if it comes to
it — roll back a release. Nothing on this page should require reading source code.

---

## `sprint-1.3-stable` — 2026-02-06

| Field | Value |
|---|---|
| **Git commit hash** | (populated on merge — capture from `git rev-parse HEAD`) |
| **Branch** | `sprint/1.3-stable` (merged into `main`) |
| **Git tag** | `sprint-1.3-stable` (lightweight, on `main`) |
| **Migration head** | `005` — Inventory + stock valuation view |
| **Migrations included** | `001 → 005` (extensions & enums · identity core · master data · catalog · inventory) |
| **Database schema version** | 34 tables, 101 foreign keys, 718 CHECK constraints, 117 indexes |
| **API version** | v1 |
| **OpenAPI operations** | 23 (18 paths) — snapshot at `docs/api/openapi.{json,yaml}` |
| **Postman collection** | 23 requests in 7 folders — `docs/api/postman_collection.json` |
| **Test summary** | **120 / 120 passed** in ~12 s under pytest-xdist (2 workers, `loadscope`) |
| **Coverage summary** | Not measured yet — `pytest-cov` will be introduced in Sprint 1.5 alongside CI cost tracking |

### Dependency versions

**Backend (`backend/requirements.txt`)**

```
fastapi==0.139.0
uvicorn[standard]==0.32.1
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
psycopg2-binary==2.9.10
alembic==1.14.0
pydantic==2.10.3
pydantic-settings==2.6.1
python-dotenv==1.2.2
pyjwt[crypto]==2.13.0
python-multipart==0.0.31
starlette==1.3.1
structlog==24.4.0
httpx==0.28.1
deepdiff==8.6.2
pytest==9.0.3
pytest-asyncio==1.4.0
pytest-xdist==3.6.1
```

**Frontend (`frontend/package.json`)** — legacy, frozen per `docs/DEPRECATED.md`.
Lockfile at `frontend/yarn.lock` (committed for deterministic builds).

### Docker image versions

- Base: `python:3.11-slim-bookworm`
- Postgres: `postgres:15-alpine`
- Node (frontend build): `node:20-alpine`

No pushed image registry yet — images are built at compose time until Sprint 1.7 introduces
a release pipeline.

### Verification gates (all green at tag)

| Gate | Result |
|---|---|
| ruff (`E, F, W, I, B`) on backend/app + tests + migrations + scripts | 0 issues |
| MyPy-strict on `app/` | 0 issues in 41 files |
| Bandit on `app/` | 0 findings across 3 241 LOC |
| pip-audit on `requirements.txt` | 0 known CVEs |
| pytest | 120 passed |
| Alembic `upgrade head → downgrade base → upgrade head` on scratch DB | ends at `005` |
| `alembic check` | 0 drift |
| Seed idempotency (×2) | identical counts |
| OpenAPI + Postman drift | baseline matches |
| Health `/api/v1/health/{live,ready,db}` | 200 · `alembic_revision=005, tables=34` |
| E2E auth (`mint_token → /auth/me`) | 200 |

### Known issues at tag

- **TD-01** — 22 FK columns lack supporting B-tree indexes. Deferred to Sprint 1.6 per PRD.
- **TD-02** — Legacy React storefront is frozen; scheduled for wholesale rebuild in Sprint 2.
- **TD-03** — No rate limiting on `/api/v1/auth/*`. Deferred to Sprint 1.5.
- **TD-04** — Supabase RLS policies not yet enabled. Deferred to Sprint 1.6.
- **TD-05** — `SUPABASE_JWT_SECRET` is the dev placeholder. Must be rotated before staging.

Full detail: `docs/TECHNICAL_DEBT.md`.

### Rollback procedure

If a Sprint 1.4+ push breaks `main` and we need to revert to this checkpoint:

```bash
# 1. Cut a hotfix branch from the tag.
git checkout -b hotfix/rollback-to-1.3-stable sprint-1.3-stable

# 2. Force-migrate the DB back to Sprint 1.3 head. WARNING: this drops
#    all Sprint 1.4+ tables. Take a backup first.
pg_dump -h $DB_HOST -U kaya kaya_bos > /tmp/pre-rollback.sql
alembic downgrade 005   # Sprint 1.3 head

# 3. Redeploy the containers pinned to this tag.
docker compose down
git checkout sprint-1.3-stable
docker compose up --build -d

# 4. Verify health.
curl $APP_URL/api/v1/health/db
# Expect: {"alembic_revision":"005","table_count":34,...}

# 5. Open a post-mortem PR referencing the failing Sprint 1.4+ commit.
```

Data loss expectation: any rows written to Sprint-1.4-introduced tables are dropped by the
downgrade. Everything captured by the Sprint 1.3 schema (users, roles, permissions, audit,
catalog, inventory) survives.

---

## Template for future checkpoints (copy this block for `sprint-1.4-stable`, …)

```markdown
## `sprint-X.Y-stable` — YYYY-MM-DD

| Field | Value |
|---|---|
| Git commit hash | |
| Branch | |
| Git tag | |
| Migration head | |
| Migrations included | |
| Database schema version | |
| API version | |
| OpenAPI operations | |
| Postman collection | |
| Test summary | |
| Coverage summary | |

### Dependency versions
### Docker image versions
### Verification gates
### Known issues
### Rollback procedure
```
