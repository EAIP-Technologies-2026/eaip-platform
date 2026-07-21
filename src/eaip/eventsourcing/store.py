"""In-memory event store implementation."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from eaip.eventsourcing.exceptions import EventStoreError
from eaip.eventsourcing.models import EventStream, StoredEvent
from eaip.logging.context import get_logger


class EventStore:
    def __init__(self) -> None:
        self._events: dict[str, StoredEvent] = {}
        self._aggregate_events: dict[str, list[str]] = {}
        self._log = get_logger("eaip.eventsourcing.store")

    def append_event(
        self,
        aggregate_type: str,
        aggregate_id: str,
        event: dict[str, Any] | StoredEvent,
        *,
        correlation_id: str = "",
        causation_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> StoredEvent:
        aggregate_key = f"{aggregate_type}:{aggregate_id}"
        existing = self._aggregate_events.get(aggregate_key, [])
        version = len(existing) + 1

        if isinstance(event, StoredEvent):
            stored = StoredEvent(
                id=event.id or str(uuid4()),
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                event_type=event.event_type,
                event_data=event.event_data,
                metadata={**(metadata or {}), **event.metadata},
                version=version,
                correlation_id=correlation_id or event.correlation_id,
                causation_id=causation_id or event.causation_id,
            )
        else:
            event_type = event.pop("event_type", "unknown")
            stored = StoredEvent(
                id=str(uuid4()),
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                event_type=event_type,
                event_data=event,
                metadata=metadata or {},
                version=version,
                correlation_id=correlation_id,
                causation_id=causation_id,
            )

        self._events[stored.id] = stored
        self._aggregate_events.setdefault(aggregate_key, []).append(stored.id)

        self._log.debug(
            "event.stored",
            event_id=stored.id,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            version=version,
        )
        return stored

    def get_events(self, aggregate_type: str, aggregate_id: str) -> list[StoredEvent]:
        aggregate_key = f"{aggregate_type}:{aggregate_id}"
        event_ids = self._aggregate_events.get(aggregate_key, [])
        return [self._events[eid] for eid in event_ids if eid in self._events]

    def get_event_stream(self, aggregate_type: str, aggregate_id: str) -> EventStream:
        events = self.get_events(aggregate_type, aggregate_id)
        return EventStream(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            events=tuple(events),
            current_version=len(events),
        )

    def get_events_by_type(
        self,
        event_type: str,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[StoredEvent]:
        result = []
        for stored in self._events.values():
            if stored.event_type != event_type:
                continue
            if since is not None and stored.timestamp < since:
                continue
            result.append(stored)
        result.sort(key=lambda e: e.timestamp)
        if limit > 0:
            return result[:limit]
        return result

    def get_aggregate_ids(self, aggregate_type: str) -> list[str]:
        ids: set[str] = set()
        for key in self._aggregate_events:
            atype, _, aid = key.partition(":")
            if atype == aggregate_type:
                ids.add(aid)
        return sorted(ids)

    def get_events_since(self, event_id: str, limit: int = 100) -> list[StoredEvent]:
        if event_id not in self._events:
            raise EventStoreError(f"Event {event_id} not found")

        start_event = self._events[event_id]
        result = []
        for stored in sorted(self._events.values(), key=lambda e: (e.timestamp, e.id)):
            if (stored.timestamp, stored.id) > (start_event.timestamp, start_event.id):
                result.append(stored)
        if limit > 0:
            return result[:limit]
        return result

    def get_event_by_id(self, event_id: str) -> StoredEvent | None:
        return self._events.get(event_id)

    def count_events(self) -> int:
        return len(self._events)


__all__ = ["EventStore"]
