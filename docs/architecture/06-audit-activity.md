# 06 — Audit Log & Activity Log Architecture

## Distinction
| | Audit Log | Activity Log |
|---|---|---|
| Purpose | Compliance, forensics, dispute resolution | UX & analytics, user timeline, "recent actions" |
| Scope | Every WRITE on protected entities | Reads, navigation, business events (login, viewed report) |
| Volume | Low-medium | High |
| Retention | 7 years (finance rule) | 90 days (rolling), then aggregated |
| Immutability | Append-only, DB-level trigger blocks UPDATE/DELETE | Append-only but purgeable |
| Structure | Structured (before/after JSONB) | Semi-structured (event + payload) |

## `audit_logs`
```
id            UUID PK
actor_id      UUID FK -> users(id)   NULL if system
actor_role    TEXT                   (denormalized snapshot)
entity        TEXT     e.g. 'order', 'invoice', 'product'
entity_id     UUID
action        TEXT     'create'|'update'|'delete'|'restore'|'void'|'refund'|'status_change'
before        JSONB    NULL for creates
after         JSONB    NULL for deletes
diff          JSONB    computed: keys that changed (server-side)
ip            INET
user_agent    TEXT
request_id    TEXT     correlates with X-Request-Id
at            TIMESTAMPTZ DEFAULT now()
```

Trigger: `BEFORE UPDATE OR DELETE ON audit_logs FOR EACH ROW EXECUTE FUNCTION raise_immutable();`

## `activity_logs`
```
id          UUID PK
actor_id    UUID NULL
event       TEXT     e.g. 'user.login', 'report.viewed', 'cart.updated', 'search.performed'
entity      TEXT NULL
entity_id   UUID NULL
payload     JSONB
ip          INET
at          TIMESTAMPTZ DEFAULT now()
```

## Write path
1. Service layer wraps every mutating operation in an `AuditContext`:
   ```python
   async with AuditContext(actor=user, entity="order", entity_id=order.id, action="update") as ctx:
       ctx.before = order.to_dict()
       ... mutation ...
       ctx.after = order.to_dict()
   ```
2. On context exit, an `audit_logs` row is INSERTed in the **same transaction** as the business write (guarantees atomicity — no orphan audits, no missed audits).
3. `diff` is computed via `deepdiff` and stored.

## Query patterns supported
- "Show me every change to invoice INV-XYZ" → `WHERE entity='invoice' AND entity_id=?`
- "What did user U do yesterday?" → `WHERE actor_id=? AND at BETWEEN ?`
- "Who deleted product P?" → `WHERE entity='product' AND entity_id=? AND action='delete'`
- All indexed by `(entity, entity_id, at DESC)` and `(actor_id, at DESC)`.

## Storage strategy
- Partitioned by month (`audit_logs_2026_02`, `_03`, …) — declarative partitioning applied at S12 hardening.
- Yearly hot table + archived tables → S3 cold storage (later).

## UI surfaces
- **User detail page** → activity timeline (last 90 days).
- **Entity detail** (order, invoice, product) → "History" tab with audit diff renderer.
- **Super Admin** → global audit search with entity + actor + date filters + CSV export.
