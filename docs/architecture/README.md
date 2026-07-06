# Kaya's Herbals BOS — Architecture Index

All architecture documents for the Business Operating System. Frozen at Sprint 1 prep. Any change requires an ADR in `/docs/adr/`.

1. [Entity Relationship Overview](01-database-erd.md)
2. [Complete PostgreSQL Schema](02-database-schema.md)
3. [SQLAlchemy Models & Alembic Migration Plan](03-sqlalchemy-alembic.md)
4. [Supabase Row-Level Security Policies](04-rls-policies.md)
5. [RBAC Design & Permission Matrix](05-rbac.md)
6. [Audit Log & Activity Log Architecture](06-audit-activity.md)
7. [Business Rules](07-business-rules.md)
8. [Master Data Module](08-master-data.md)

## How to read
Start with (1) for the mental map, (7) for the invariants, then (2)+(3) for the physical layer. (4)+(5)+(6) describe security and traceability. (8) is the reference data foundation.

## What is NOT here yet (deferred to their sprint)
- Payment reconciliation state machine — Sprint 7
- Shipping-carrier adapter contracts — Sprint 6/10
- Notification templates catalogue — Sprint 10
- Reporting query catalogue — Sprint 11
- Backup / DR runbook — Sprint 12

## Approval
When you say **"Architecture approved — start Sprint 1"**, I will:
1. Create the FastAPI app skeleton + `db/base` + mixins.
2. Author all Alembic migrations (`001` → `012`).
3. Wire Supabase Auth ↔ RBAC bridge.
4. Seed permissions, roles, master data.
5. Deliver Sprint 1 demo video + updated OpenAPI docs.

No migrations will run and no models will be created before that message.
