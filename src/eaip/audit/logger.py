"""Immutable in-memory audit logger — records, queries, and exports audit events."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from eaip.audit.exceptions import AuditEventNotFoundError
from eaip.audit.models import AuditEvent, Severity
from eaip.logging.context import get_logger


class AuditLogger:
    def __init__(self) -> None:
        self._store: dict[str, AuditEvent] = {}
        self._log = get_logger("eaip.audit.logger")

    async def log(self, event: AuditEvent) -> AuditEvent:
        self._store[event.id] = event
        self._log.info("audit.event.logged", event_id=event.id, event_type=event.event_type)
        return event

    async def log_action(
        self,
        actor_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        *,
        event_type: str = "audit.action",
        actor_type: str = "user",
        details: dict[str, Any] | None = None,
        severity: Severity = Severity.INFO,
        correlation_id: str = "",
        ip_address: str = "",
        user_agent: str = "",
        session_id: str = "",
        tags: tuple[str, ...] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        import uuid

        event = AuditEvent(
            id=str(uuid.uuid4()),
            event_type=event_type,
            actor_id=actor_id,
            actor_type=actor_type,  # type: ignore[arg-type]
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            severity=severity,
            correlation_id=correlation_id,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            tags=tuple(tags) if tags else (),
            metadata=metadata or {},
        )
        return await self.log(event)

    async def query(self, filters: dict[str, Any]) -> list[AuditEvent]:
        results: list[AuditEvent] = list(self._store.values())
        for key, value in filters.items():
            if key == "event_type":
                results = [e for e in results if e.event_type == value]
            elif key == "actor_id":
                results = [e for e in results if e.actor_id == value]
            elif key == "actor_type":
                results = [e for e in results if e.actor_type.value == value]
            elif key == "action":
                results = [e for e in results if e.action == value]
            elif key == "resource_type":
                results = [e for e in results if e.resource_type == value]
            elif key == "resource_id":
                results = [e for e in results if e.resource_id == value]
            elif key == "severity":
                results = [e for e in results if e.severity.value == value]
            elif key == "correlation_id":
                results = [e for e in results if e.correlation_id == value]
        return results

    async def get_by_id(self, event_id: str) -> AuditEvent:
        event = self._store.get(event_id)
        if event is None:
            raise AuditEventNotFoundError(f"Audit event {event_id!r} not found")
        return event

    async def get_by_resource(self, resource_type: str, resource_id: str) -> list[AuditEvent]:
        return [
            e
            for e in self._store.values()
            if e.resource_type == resource_type and e.resource_id == resource_id
        ]

    async def get_by_actor(self, actor_id: str) -> list[AuditEvent]:
        return [e for e in self._store.values() if e.actor_id == actor_id]

    async def get_by_timerange(self, start: datetime, end: datetime) -> list[AuditEvent]:
        return [e for e in self._store.values() if start <= e.timestamp <= end]

    async def export(self, events: list[AuditEvent], format: str = "json") -> list[dict[str, Any]]:
        if format == "json":
            return [e.model_dump() for e in events]
        if format == "dict":
            return [dict(e) for e in events]
        msg = f"Unsupported export format: {format!r}"
        raise ValueError(msg)


__all__ = ["AuditLogger"]
