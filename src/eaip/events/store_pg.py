"""PostgreSQL-backed event store — durable, tenant-scoped event log.

The in-process :class:`~eaip.events.store.EventStore` keeps a bounded deque for
the live activity feed.  ``PgEventStore`` provides the durable counterpart
required by BATCH 01 (Point 03): events are appended to the ``runtime_events``
table via the shared :class:`~eaip.infrastructure.db.connection.DatabaseConnection`
pool, survive process restarts, and can be queried by type / entity id / tenant.

The public surface mirrors :class:`~eaip.events.store.EventStore` (``record``,
``recent``, ``recent_by``) so consumers can swap the backing store without
changing call sites.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any

from eaip.events.errors import EventError
from eaip.events.event import DomainEvent
from eaip.infrastructure.db.connection import DatabaseConnection
from eaip.logging.context import get_logger

log = get_logger("eaip.events.store_pg")


class EventStoreError(EventError):
    """Raised when the durable event store cannot fulfil an operation."""


def _camel_to_title(name: str) -> str:
    clean = name.lstrip("_")
    return re.sub(r"(?<!^)(?=[A-Z])", " ", clean)


def _determine_status(type_name: str) -> str:
    upper = type_name.upper()
    if any(w in upper for w in ["FAIL", "ERROR", "TIMEOUT"]):
        return "error"
    if any(w in upper for w in ["SUCCESS", "COMPLETE", "FINISHED"]):
        return "success"
    if any(w in upper for w in ["WARN", "DEGRADED"]):
        return "warning"
    return "info"


def _classify_module(module: str) -> str:
    if "agents" in module:
        return "agent"
    if "workflow" in module:
        return "workflow"
    if "knowledge" in module:
        return "knowledge"
    if "auth" in module:
        return "auth"
    if "mission" in module:
        return "mission"
    return "system"


def _build_message_from_dict(event_type: str, payload: dict[str, Any]) -> str:
    skip_keys = {"occurred_at", "correlation_id", "event_type", "tenant_id"}
    fields = {k: v for k, v in payload.items() if k not in skip_keys and not k.startswith("_")}
    if not fields:
        return event_type
    parts: list[str] = []
    for k, v in fields.items():
        if isinstance(v, (str, int, float, bool)):
            parts.append(f"{k}={v}")
        else:
            parts.append(f"{k}={type(v).__name__}")
    return ", ".join(parts[:5])


class PgEventStore:
    """Durable event store backed by the ``runtime_events`` PostgreSQL table."""

    def __init__(self, maxlen: int = 0) -> None:
        # ``maxlen`` is accepted for interface compatibility with
        # :class:`~eaip.events.store.EventStore`; durability is unbounded and
        # retention is governed by the event retention module, not a deque.
        del maxlen

    def _require_db(self) -> None:
        if DatabaseConnection.get_pool() is None:
            raise EventStoreError(
                "PgEventStore requires an initialized DatabaseConnection pool. "
                "Call DatabaseConnection.initialize() first."
            )

    async def record(self, event: DomainEvent) -> None:
        """Append ``event`` to the durable event log.

        The event's stable ``id`` is used as the row primary key, so re-recording
        the same event instance is a no-op (idempotent).
        """
        self._require_db()
        data = _safe_dump(event)
        metadata = {
            "classified_type": self._classify(event),
            "agent_id": data.get("agent_id"),
            "workflow_id": data.get("workflow_id"),
            "run_id": data.get("run_id"),
            "mission_id": data.get("mission_id"),
        }
        correlation = str(event.correlation_id) if event.correlation_id else None
        await DatabaseConnection.execute(
            """
            INSERT INTO runtime_events
                (id, event_type, source, payload, metadata, correlation_id,
                 tenant_id, created_at)
            VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6, $7, $8)
            ON CONFLICT (id) DO NOTHING
            """,
            event.id,
            type(event).__name__,
            type(event).__module__,
            event.model_dump_json(),
            json.dumps(metadata),
            correlation,
            event.tenant_id,
            event.occurred_at,
        )

    async def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return the most recent events, newest first."""
        self._require_db()
        rows = await DatabaseConnection.fetch(
            """
            SELECT id, event_type, source, payload, metadata, tenant_id, created_at
            FROM runtime_events
            ORDER BY created_at DESC
            LIMIT $1
            """,
            limit,
        )
        return [_row_to_activity(row) for row in rows]

    async def recent_by(
        self,
        *,
        agent_id: str | None = None,
        workflow_id: str | None = None,
        mission_id: str | None = None,
        type: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Return recent events filtered by entity id / classified type."""
        self._require_db()
        clauses: list[str] = []
        params: list[Any] = []
        if agent_id is not None:
            params.append(agent_id)
            clauses.append(f"metadata->>'agent_id' = ${len(params)}")
        if workflow_id is not None:
            params.append(workflow_id)
            clauses.append(f"metadata->>'workflow_id' = ${len(params)}")
        if mission_id is not None:
            params.append(mission_id)
            clauses.append(f"metadata->>'mission_id' = ${len(params)}")
        if type is not None:
            params.append(type)
            clauses.append(f"metadata->>'classified_type' = ${len(params)}")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        rows = await DatabaseConnection.fetch(
            f"""
            SELECT id, event_type, source, payload, metadata, tenant_id, created_at
            FROM runtime_events
            {where}
            ORDER BY created_at DESC
            LIMIT ${len(params)}
            """,
            *params,
        )
        return [_row_to_activity(row) for row in rows]

    async def recent_by_tenant(
        self, tenant_id: str, *, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Return recent events for a single tenant (isolation helper)."""
        self._require_db()
        rows = await DatabaseConnection.fetch(
            """
            SELECT id, event_type, source, payload, metadata, tenant_id, created_at
            FROM runtime_events
            WHERE tenant_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            tenant_id,
            limit,
        )
        return [_row_to_activity(row) for row in rows]

    async def count(self, *, tenant_id: str | None = None) -> int:
        """Total recorded events, optionally scoped to a tenant."""
        self._require_db()
        if tenant_id is None:
            return await DatabaseConnection.fetchval("SELECT COUNT(*) FROM runtime_events")
        return await DatabaseConnection.fetchval(
            "SELECT COUNT(*) FROM runtime_events WHERE tenant_id = $1", tenant_id
        )

    async def stored_events(
        self,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
        event_type: str | None = None,
        tenant_id: str | None = None,
        limit: int = 0,
    ) -> list[dict[str, Any]]:
        """Return stored events for replay/projection workloads.

        Results are ordered by ``created_at`` ascending.  ``limit <= 0`` means
        no limit.  Tenant-scoping is enforced when ``tenant_id`` is provided.
        """
        self._require_db()
        clauses: list[str] = []
        params: list[Any] = []
        if since is not None:
            params.append(since)
            clauses.append(f"created_at >= ${len(params)}")
        if until is not None:
            params.append(until)
            clauses.append(f"created_at <= ${len(params)}")
        if event_type is not None:
            params.append(event_type)
            clauses.append(f"event_type = ${len(params)}")
        if tenant_id is not None:
            params.append(tenant_id)
            clauses.append(f"tenant_id = ${len(params)}")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"""
            SELECT id, event_type, source, payload, metadata, correlation_id,
                   tenant_id, created_at
            FROM runtime_events
            {where}
            ORDER BY created_at ASC
        """
        if limit > 0:
            params.append(limit)
            sql += f" LIMIT ${len(params)}"
        rows = await DatabaseConnection.fetch(sql, *params)
        return [_row_to_stored(row) for row in rows]

    @staticmethod
    def _classify(event: DomainEvent) -> str:
        return _classify_module(type(event).__module__)


def _safe_dump(event: DomainEvent) -> dict[str, Any]:
    try:
        return event.model_dump()
    except Exception:
        return {}


def _row_to_activity(row: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if row["payload"]:
        try:
            payload = json.loads(row["payload"]) if isinstance(row["payload"], str) else row["payload"]
        except (json.JSONDecodeError, TypeError):
            payload = {}
    metadata = _as_dict(row["metadata"])
    event_type = row["event_type"]
    timestamp = row["created_at"]
    occurred = payload.get("occurred_at")
    if isinstance(occurred, str):
        timestamp = occurred
    return {
        "id": row["id"],
        "type": metadata.get("classified_type") or _classify_module(row["source"]),
        "action": _camel_to_title(event_type),
        "message": _build_message_from_dict(event_type, payload),
        "timestamp": _iso(timestamp),
        "status": _determine_status(event_type),
        "tenant_id": row.get("tenant_id"),
    }


def _iso(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return datetime.now(UTC).isoformat()


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return {}
    return value or {}


def _row_to_stored(row: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if row["payload"]:
        try:
            payload = json.loads(row["payload"]) if isinstance(row["payload"], str) else row["payload"]
        except (json.JSONDecodeError, TypeError):
            payload = {}
    return {
        "id": row["id"],
        "event_type": row["event_type"],
        "source": row["source"],
        "payload": payload,
        "metadata": _as_dict(row["metadata"]),
        "correlation_id": row["correlation_id"],
        "tenant_id": row["tenant_id"],
        "occurred_at": row["created_at"],
    }


__all__ = ["EventStoreError", "PgEventStore"]