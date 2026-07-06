# 002 — Identity core

**Revision**: `002` &nbsp;·&nbsp; **Parent**: `001` &nbsp;·&nbsp; **Sprint**: 1.1

## Tables created
| Table | Rows expected | Notes |
|---|---|---|
| `users` | O(10²)–O(10⁶) | PK **not** auto-generated — value comes from Supabase `auth.users.id`. `email` is `UNIQUE`. `status` uses the `user_status` enum from migration 001. Includes soft-delete columns + version. |
| `roles` | ~15 | Seeded in Sprint 1.6. `code` is `UNIQUE` (e.g. `super_admin`, `catalog_manager`). |
| `permissions` | ~120 | Static seed. `code` follows `<module>.<action>` (e.g. `orders.refund`). |
| `role_permissions` | many | Composite PK `(role_id, permission_id)` — PK enforces uniqueness. |
| `user_roles` | many | Composite PK `(user_id, role_id)` + `assigned_by / assigned_at`. |
| `sessions` | high volume | Tracks Supabase refresh sessions by `jti`. `revoked_at` enables force-logout (BR-USR-04). |
| `user_invitations` | low | Single-use invite tokens with `expires_at`. |
| `audit_logs` | very high volume | Wide row: `actor_id / entity / entity_id / action / before / after / diff / ip / user_agent / request_id / at`. Immutability trigger added in migration 012. |
| `activity_logs` | very high volume | Read/navigation event stream: `actor_id / event / entity / entity_id / payload / ip / at`. Purgeable. |

## Indexes
- `ix_users_email`, `ix_users_status`
- `ix_roles_code`, `ix_permissions_code`, `ix_permissions_module`
- `ix_sessions_user_id`, `ix_sessions_jti`
- `ix_user_invitations_email`, `ix_user_invitations_token`
- `ix_audit_logs_entity` (composite `(entity, entity_id, at)`), `ix_audit_logs_actor_id` (composite `(actor_id, at)`), `ix_audit_logs_at`
- `ix_activity_logs_actor_id` (composite `(actor_id, at)`), `ix_activity_logs_event` (composite `(event, at)`)

## Foreign-key strategy
- `users.deleted_by → users.id` is added via `use_alter=True` so migration order still works.
- `sessions.user_id`, `user_roles.user_id`, `audit_logs.actor_id`, `activity_logs.actor_id` — all `ON DELETE SET NULL` except `sessions` and PKs which cascade (a user's sessions/role assignments disappear with the user, but their historical logs are preserved with `actor_id = NULL`).
- `user_invitations.role_id → roles.id` is `ON DELETE RESTRICT` — you can't delete a role that has pending invitations.

## Downgrade
Fully reversible; tables dropped in reverse dependency order. The `user_status` enum is **not** dropped here — it belongs to migration 001.

## Business-rule anchors
- BR-USR-01 — Supabase Auth is the sole authentication source. `users.password` intentionally absent.
- BR-USR-04 — Suspending a user requires revoking sessions (`sessions.revoked_at`).
- BR-USR-05 — Last active Super Admin protection is enforced at the service layer (Sprint 1.6), not by DB constraint.
- Audit / activity distinction — see `docs/architecture/06-audit-activity.md`.

## Verified via
- Round-trip: `upgrade head → downgrade base → upgrade head`
- `alembic check` (no drift)
- 20 pytest cases (`tests/test_models_schema.py`) covering timestamp/soft-delete/UUID conventions per table
