"""Event replay service — replay events through handlers for recovery or projection building."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime

from eaip.eventsourcing.exceptions import ReplayError
from eaip.eventsourcing.models import StoredEvent
from eaip.eventsourcing.store import EventStore
from eaip.logging.context import get_logger

ReplayHandler = Callable[[StoredEvent], Awaitable[None]]


class EventReplayService:
    def __init__(self, store: EventStore) -> None:
        self._store = store
        self._log = get_logger("eaip.eventsourcing.replay")

    async def replay_aggregate(
        self,
        aggregate_type: str,
        aggregate_id: str,
        handlers: list[ReplayHandler],
    ) -> int:
        events = self._store.get_events(aggregate_type, aggregate_id)
        if not events:
            raise ReplayError(f"No events found for {aggregate_type}:{aggregate_id}")

        count = 0
        for event in events:
            for handler in handlers:
                await handler(event)
                count += 1
        return count

    async def replay_event_type(
        self,
        event_type: str,
        handlers: list[ReplayHandler],
        since: datetime | None = None,
    ) -> int:
        events = self._store.get_events_by_type(event_type, since=since, limit=0)
        count = 0
        for event in events:
            for handler in handlers:
                await handler(event)
                count += 1
        return count

    async def replay_all(
        self,
        handlers: list[ReplayHandler],
        since: datetime | None = None,
    ) -> int:
        if since:
            events = []
            for stored in [
                self._store.get_events_by_type(et, since=since, limit=0)
                for et in self._get_all_event_types()
            ]:
                events.extend(stored)
            events.sort(key=lambda e: (e.timestamp, e.id))
        else:
            stored_events = []
            for et in self._get_all_event_types():
                stored_events.extend(self._store.get_events_by_type(et, limit=0))
            events = sorted(stored_events, key=lambda e: (e.timestamp, e.id))

        count = 0
        for event in events:
            for handler in handlers:
                await handler(event)
                count += 1
        return count

    async def replay_range(
        self,
        start_id: str,
        end_id: str,
        handlers: list[ReplayHandler],
    ) -> int:
        start_event = self._store.get_event_by_id(start_id)
        end_event = self._store.get_event_by_id(end_id)
        if start_event is None:
            raise ReplayError(f"Start event {start_id} not found")
        if end_event is None:
            raise ReplayError(f"End event {end_id} not found")

        events = []
        for stored in sorted(self._store._events.values(), key=lambda e: (e.timestamp, e.id)):
            if (stored.timestamp, stored.id) >= (start_event.timestamp, start_event.id) and (
                stored.timestamp,
                stored.id,
            ) <= (end_event.timestamp, end_event.id):
                events.append(stored)

        count = 0
        for event in events:
            for handler in handlers:
                await handler(event)
                count += 1
        return count

    def _get_all_event_types(self) -> list[str]:
        types: set[str] = set()
        for event in self._store._events.values():
            types.add(event.event_type)
        return sorted(types)


__all__ = ["EventReplayService"]
