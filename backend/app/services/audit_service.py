"""AuditContext — records before/after JSONB on every write action.

Usage:
    async with AuditContext(db, actor=user, entity="product", entity_id=p.id, action="update", request_id=rid) as ctx:
        ctx.before = _snapshot(p)
        ...mutate...
        ctx.after = _snapshot(p)

The context inserts a single `audit_logs` row on __aexit__(no-exception),
using `deepdiff` to compute the field-level diff. All writes happen on the
same AsyncSession as the business mutation, guaranteeing atomicity.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.models.identity import ActivityLog, AuditLog
from deepdiff import DeepDiff
from sqlalchemy.ext.asyncio import AsyncSession


def _to_serializable(value: Any) -> Any:
    """JSONB-safe conversion for common non-json types."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {k: _to_serializable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_to_serializable(v) for v in value]
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


@dataclass
class AuditContext:
    db: AsyncSession
    entity: str
    action: str
    entity_id: uuid.UUID | None = None
    actor_id: uuid.UUID | None = None
    actor_role: str | None = None
    ip: str | None = None
    user_agent: str | None = None
    request_id: str | None = None
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    _flushed: bool = field(default=False, init=False)

    async def __aenter__(self) -> "AuditContext":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            return  # do not persist audit rows for failed operations
        diff = None
        if self.before is not None and self.after is not None:
            try:
                dd = DeepDiff(self.before, self.after, ignore_order=True, view="tree")
                diff = _to_serializable(dd.to_dict()) or None
            except Exception:  # pragma: no cover — best-effort diff
                diff = None
        row = AuditLog(
            actor_id=self.actor_id,
            actor_role=self.actor_role,
            entity=self.entity,
            entity_id=self.entity_id,
            action=self.action,
            before=_to_serializable(self.before) if self.before is not None else None,
            after=_to_serializable(self.after) if self.after is not None else None,
            diff=diff,
            ip=self.ip,
            user_agent=self.user_agent,
            request_id=self.request_id,
        )
        self.db.add(row)
        await self.db.flush()
        self._flushed = True


async def log_activity(
    db: AsyncSession,
    *,
    event: str,
    actor_id: uuid.UUID | None = None,
    entity: str | None = None,
    entity_id: uuid.UUID | None = None,
    payload: dict[str, Any] | None = None,
    ip: str | None = None,
) -> None:
    """Fire-and-forget activity log — no diff, no before/after."""
    db.add(
        ActivityLog(
            actor_id=actor_id,
            event=event,
            entity=entity,
            entity_id=entity_id,
            payload=_to_serializable(payload) if payload is not None else None,
            ip=ip,
        )
    )
    await db.flush()
