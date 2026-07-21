"""Immutable audit event store — append-only, time-ordered, retention-managed."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from eaip.audit.events import AuditStoreCleaned, AuditStoreSnapshotCreated
from eaip.audit.models import AuditEvent
from eaip.shared.time import utc_now


class AuditStoreConfig:
    max_events: int = 100000
    retention_days: int = 365
    snapshot_interval: int = 10000


class ImmutableAuditStore:
    def __init__(self, config: AuditStoreConfig | None = None) -> None:
        self._config = config or AuditStoreConfig()
        self._events: list[AuditEvent] = []
        self._snapshots: dict[int, str] = {}
        self._snapshot_counter: int = 0
        self._event_bus: Any = None

    def set_event_bus(self, bus: Any) -> None:
        self._event_bus = bus

    def append(self, event: AuditEvent) -> AuditEvent:
        self._events.append(event)

        if len(self._events) % self._config.snapshot_interval == 0:
            self._create_snapshot()

        return event

    def query(
        self,
        *,
        actor: str | None = None,
        action: str | None = None,
        resource: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEvent]:
        results = list(self._events)

        if actor:
            results = [e for e in results if e.actor_id == actor]
        if action:
            results = [e for e in results if e.action == action]
        if resource:
            results = [e for e in results if e.resource_type == resource]
        if start_time:
            results = [e for e in results if e.timestamp >= start_time]
        if end_time:
            results = [e for e in results if e.timestamp <= end_time]

        return results[offset : offset + limit]

    def count(
        self,
        *,
        actor: str | None = None,
        action: str | None = None,
        resource: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> int:
        return len(
            self.query(
                actor=actor,
                action=action,
                resource=resource,
                start_time=start_time,
                end_time=end_time,
                limit=10**9,
                offset=0,
            )
        )

    def get_snapshot(self, index: int) -> str | None:
        return self._snapshots.get(index)

    def get_snapshot_count(self) -> int:
        return len(self._snapshots)

    def size(self) -> int:
        return len(self._events)

    def cleanup(self) -> int:
        cutoff = utc_now() - timedelta(days=self._config.retention_days)
        before = len(self._events)
        self._events = [e for e in self._events if e.timestamp >= cutoff]
        removed = before - len(self._events)

        if self._event_bus is not None:
            import asyncio

            try:
                asyncio.ensure_future(
                    self._event_bus.publish(
                        AuditStoreCleaned(
                            events_removed=removed,
                            remaining=len(self._events),
                        )
                    )
                )
            except Exception:
                pass

        return removed

    def _create_snapshot(self) -> None:
        idx = len(self._events)
        summary = f"snapshot at event {idx}: {idx} total events"
        self._snapshots[idx] = summary
        self._snapshot_counter += 1

        if self._event_bus is not None:
            import asyncio

            try:
                asyncio.ensure_future(
                    self._event_bus.publish(
                        AuditStoreSnapshotCreated(
                            event_count=idx,
                            snapshot_index=self._snapshot_counter,
                        )
                    )
                )
            except Exception:
                pass


__all__ = ["AuditStoreConfig", "ImmutableAuditStore"]
