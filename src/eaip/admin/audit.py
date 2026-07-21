"""Audit logger — records and queries audit trail entries."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from eaip.admin.events import AuditEntryCreated
from eaip.admin.models import AuditEntry
from eaip.events.bus import EventBus
from eaip.logging.context import get_logger
from eaip.shared.identifiers import CorrelationId


class AuditLogger:
    """Records audit entries in memory and optionally publishes to an event bus.

    Supports filtering by actor, action, resource type, and time range.
    """

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Initialize an AuditLogger.

        Args:
            event_bus: Optional event bus to publish AuditEntryCreated events.
        """
        self._store: dict[str, AuditEntry] = {}
        self._event_bus = event_bus
        self._log = get_logger("eaip.admin.audit")

    def log(self, entry: AuditEntry) -> None:
        """Record an audit entry in the in-memory store.

        Args:
            entry: The audit entry to record.
        """
        self._store[entry.id] = entry
        self._log.info("audit.entry_recorded", entry_id=entry.id, action=entry.action)

    async def publish(self, entry: AuditEntry) -> None:
        """Record an audit entry and publish an AuditEntryCreated event.

        Args:
            entry: The audit entry to record and publish.
        """
        self.log(entry)
        if self._event_bus is not None:
            event = AuditEntryCreated(
                entry_id=entry.id,
                actor_id=entry.actor_id,
                action=entry.action,
                resource_type=entry.resource_type,
                resource_id=entry.resource_id,
                outcome=entry.outcome.value,
                correlation_id=CorrelationId(entry.correlation_id)
                if entry.correlation_id
                else None,
            )
            await self._event_bus.publish(event)
            self._log.debug("audit.event_published", entry_id=entry.id)

    def query(
        self,
        *,
        actor: str | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[AuditEntry]:
        """Query the audit log with optional filters.

        Args:
            actor: Filter by actor ID.
            action: Filter by action name.
            resource_type: Filter by resource type.
            start: Include entries on or after this timestamp.
            end: Include entries on or before this timestamp.

        Returns:
            A list of matching audit entries.
        """
        results: list[AuditEntry] = list(self._store.values())

        if actor is not None:
            results = [e for e in results if e.actor_id == actor]
        if action is not None:
            results = [e for e in results if e.action == action]
        if resource_type is not None:
            results = [e for e in results if e.resource_type == resource_type]
        if start is not None:
            results = [e for e in results if e.timestamp >= start]
        if end is not None:
            results = [e for e in results if e.timestamp <= end]

        results.sort(key=lambda e: e.timestamp, reverse=True)
        return results

    def export(self, start: datetime, end: datetime) -> Sequence[AuditEntry]:
        """Export audit entries within a time range.

        Args:
            start: Start of the time range (inclusive).
            end: End of the time range (inclusive).

        Returns:
            A sequence of audit entries in chronological order.
        """
        entries = [e for e in self._store.values() if start <= e.timestamp <= end]
        entries.sort(key=lambda e: e.timestamp)
        return entries

    def clear(self) -> None:
        """Clear all stored entries."""
        self._store.clear()
