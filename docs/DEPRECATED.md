# Deprecated code — pending Sprint 2 removal

_Last updated: 2026-02-06 (Sprint 1.3 stable)._

This document catalogues code that has been intentionally left on disk despite being
scheduled for removal. It exists so a fresh contributor understands **at a glance** which
files are load-bearing and which are frozen.

## 1. Legacy React storefront (`frontend/src/**`)

### Why it's still here
- It was the UI of the original Kaya's Herbals MongoDB MVP that predated the FastAPI/Postgres rewrite.
- Nothing depends on it — no backend endpoint under `/api/v1/*` is called by it. The `frontend/src/lib/api.js`
  base URL points at endpoints that no longer exist (they lived in the deleted `backend/server.py`).
- Deleting it today would leave the preview URL serving a blank React shell during Sprint 1.4–1.7, which
  slows manual UI smoke checks against the new API.

### Frozen files (do **not** refactor, do **not** run codemods, do **not** touch)
- `frontend/src/App.js`
- `frontend/src/context/AuthContext.jsx`
- `frontend/src/context/CartContext.jsx`
- `frontend/src/lib/api.js`
- `frontend/src/lib/utils.js`
- `frontend/src/layouts/StorefrontLayout.jsx`
- `frontend/src/layouts/DashboardLayout.jsx`
- `frontend/src/pages/Landing.jsx`
- `frontend/src/pages/Shop.jsx`
- `frontend/src/pages/ProductDetail.jsx`
- `frontend/src/pages/Cart.jsx`
- `frontend/src/pages/Checkout.jsx`
- `frontend/src/pages/OrderConfirmation.jsx`
- `frontend/src/pages/Login.jsx`
- `frontend/src/pages/Register.jsx`
- `frontend/src/pages/MyOrders.jsx`
- `frontend/src/pages/dashboard/*.jsx`
- `frontend/src/hooks/use-toast.js`

### Known issues (all deferred to the Sprint 2 rebuild, not fixed here)
- `localStorage`-backed JWT + cart storage (XSS-vulnerable in principle, but currently unreachable
  because the endpoints those tokens would target were deleted with `server.py`).
- 15 `useEffect` / `useCallback` dependency-array warnings from `react-hooks/exhaustive-deps`.
- Six components > 100 lines that would benefit from splitting (`StorefrontLayout`, `Landing`,
  `Checkout`, `InvoicesAdmin`, `OrdersAdmin`, `DistributorsAdmin`, `ProductsAdmin`).
- Seven `key={index}` usages during list rendering.
- Empty catch block in `AuthContext.jsx`.

These are documented in the 2026-02-06 external code review and were **not** fixed because:
1. The user's Sprint 1.3 Definition-of-Done was "do not restructure existing code unless
   absolutely necessary" (message dated 2026-02-06).
2. The Sprint 2 plan replaces this entire folder with a React 19 + Vite + TS + Tailwind +
   Shadcn/UI + TanStack Query + Zustand + Zod app (`docs/DECISIONS.md`). The new stack
   invalidates every one of the above findings by construction (server-provided session
   cookies, TanStack Query cache instead of ad-hoc `useEffect`, one-file-per-screen Zod
   schemas, stable IDs from the API).

### Planned replacement — Sprint 2
- Replace `frontend/src/**` wholesale.
- Auth token storage moves to httpOnly cookies signed by the FastAPI backend.
- Cart moves to a Zustand slice hydrated from `/api/v1/cart/*`.
- Every list uses server-provided stable IDs as React keys.

### Expected removal milestone
**Sprint 2, PR #1** — "Frontend rebuild scaffolding". The first Sprint 2 commit deletes
`frontend/src/**` and lands the new Vite project in its place. Milestone tag: `sprint-2.0-frontend-rebuild-start`.

## 2. `backend/server.py` (Mongo MVP) — **DELETED in Sprint 1.3-stable**

- Previously listed here as deprecated; deleted `2026-02-06` alongside this document as part of
  the Sprint 1.3 stable checkpoint.
- 564 LOC removed. No references remained: supervisor points at `app.main:app`, docker-compose
  points at `app.main:app`, CI runs `alembic + pytest` against the FastAPI app only.
- `requirements.txt` never listed the MVP-only deps (`motor`, `bcrypt`) — nothing to prune.

## Contract with future sprints
- Any Sprint 1.4+ code that _imports_ or _re-exposes_ anything from `frontend/src/**` must be
  rejected in code review. New pages should live in the Sprint 2 project once it lands.
- Any bug filed against a file listed in §1 is closed as `wontfix — pending sprint 2 rebuild`,
  unless it is an **actual reachable security vulnerability** in the deployed preview. Reachable
  means: the exploit path terminates in a live API call to `app.main:app` and produces a real
  effect. Purely browser-local risks in code with no working backend are not reachable.
