# Kaya's Herbals BOS — Approved Decisions & Standards

_Frozen at Sprint 0 kickoff. Any change requires an ADR in /docs/adr._

## Stack
- Monorepo: pnpm + Turborepo
- Frontend: React 19, Vite, Tailwind, Shadcn/UI, TanStack Query, Zustand, Zod
- Backend: FastAPI (Python 3.11), SQLAlchemy 2.x async, Alembic, Pydantic v2
- DB: PostgreSQL 16 (Supabase in staging/prod)
- Auth: Supabase Auth (login, verify, reset) + our RBAC
- Payments: Razorpay (UPI/GPay/PhonePe/Cards/NetBanking/Wallets)
- Email: Resend · WhatsApp: WhatsApp Cloud API
- Storage: Supabase Storage (v1)
- Hosting (prod): Vercel (frontends) + Railway/Render/DO (backend) + Supabase (DB) + Upstash Redis

## Cross-cutting standards (every module)
RBAC | Audit log (before/after) | Activity log | Search + Filter + Sort + Pagination | Excel & PDF export | Responsive UI | Server + client validation | OpenAPI docs | Unit-test-ready | Soft delete | Optimistic locking | Idempotency keys on POST | X-Request-Id correlation

## Roadmap additions (locked)
1. Multi-warehouse inventory with warehouse-specific stock.
2. Product master extras: FSSAI, AYUSH, manufacturer, shelf-life, storage, certifications.
3. Purchase & selling price history + profit-margin views.
4. Stock states: Available, Reserved, Damaged, Returned, Expired.
5. Every dashboard KPIs: Sales, Revenue, Orders, Low Stock, Near Expiry, Outstanding Payments, Top Products.
6. Every list module ships with Search + Filters + Sort + Pagination.
7. Audit logs capture actor + entity + before + after + at + ip.
8. Storefront browsable publicly; auth required only at checkout / account.

## Brand tokens (v1)
Primary green #1F3D2B · Secondary green #4C8B5A · Off-white #F8F5EE · Antique gold #C9A24B · Text #2D2D2D
Headings: Poppins · Body: Inter
