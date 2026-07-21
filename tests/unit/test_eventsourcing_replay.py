"""Tests for EventReplayService."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from eaip.eventsourcing.exceptions import ReplayError
from eaip.eventsourcing.models import StoredEvent
from eaip.eventsourcing.replay import EventReplayService
from eaip.eventsourcing.store import EventStore


class TestEventReplayService:
    @pytest.fixture
    def store(self) -> EventStore:
        return EventStore()

    @pytest.fixture
    def service(self, store: EventStore) -> EventReplayService:
        return EventReplayService(store)

    async def test_replay_aggregate(self, store: EventStore, service: EventReplayService) -> None:
        store.append_event("order", "123", {"event_type": "order.created"})
        store.append_event("order", "123", {"event_type": "order.shipped"})
        seen: list[str] = []

        async def handler(event: StoredEvent) -> None:
            seen.append(event.event_type)

        count = await service.replay_aggregate("order", "123", [handler])
        assert count == 2
        assert seen == ["order.created", "order.shipped"]

    async def test_replay_aggregate_empty(self, service: EventReplayService) -> None:
        async def handler(event: StoredEvent) -> None:
            pass

        with pytest.raises(ReplayError):
            await service.replay_aggregate("order", "nonexistent", [handler])

    async def test_replay_event_type(self, store: EventStore, service: EventReplayService) -> None:
        store.append_event("order", "1", {"event_type": "order.created"})
        store.append_event("order", "2", {"event_type": "order.created"})
        store.append_event("invoice", "1", {"event_type": "invoice.paid"})
        seen: list[str] = []

        async def handler(event: StoredEvent) -> None:
            seen.append(event.aggregate_id)

        count = await service.replay_event_type("order.created", [handler])
        assert count == 2
        assert sorted(seen) == ["1", "2"]

    async def test_replay_event_type_with_since(
        self, store: EventStore, service: EventReplayService
    ) -> None:
        store.append_event("order", "1", {"event_type": "order.created"})
        future = datetime.now(UTC)
        count = await service.replay_event_type("order.created", [], since=future)
        assert count == 0

    async def test_replay_all(self, store: EventStore, service: EventReplayService) -> None:
        store.append_event("order", "1", {"event_type": "order.created"})
        store.append_event("invoice", "1", {"event_type": "invoice.paid"})
        seen: list[str] = []

        async def handler(event: StoredEvent) -> None:
            seen.append(event.event_type)

        count = await service.replay_all([handler])
        assert count == 2
        assert "order.created" in seen
        assert "invoice.paid" in seen

    async def test_replay_range(self, store: EventStore, service: EventReplayService) -> None:
        e1 = store.append_event("order", "1", {"event_type": "order.created"})
        e2 = store.append_event("order", "1", {"event_type": "order.shipped"})
        store.append_event("order", "1", {"event_type": "order.delivered"})
        seen: list[str] = []

        async def handler(event: StoredEvent) -> None:
            seen.append(event.event_type)

        count = await service.replay_range(e1.id, e2.id, [handler])
        assert count == 2
        assert seen == ["order.created", "order.shipped"]

    async def test_replay_range_invalid_start(self, service: EventReplayService) -> None:
        async def handler(event: StoredEvent) -> None:
            pass

        with pytest.raises(ReplayError):
            await service.replay_range("bad-start", "bad-end", [handler])

    async def test_multiple_handlers(self, store: EventStore, service: EventReplayService) -> None:
        store.append_event("order", "1", {"event_type": "order.created"})
        seen1: list[str] = []
        seen2: list[str] = []

        async def handler1(event: StoredEvent) -> None:
            seen1.append(event.event_type)

        async def handler2(event: StoredEvent) -> None:
            seen2.append(event.event_type)

        count = await service.replay_aggregate("order", "1", [handler1, handler2])
        assert count == 2  # 1 event * 2 handlers
        assert seen1 == ["order.created"]
        assert seen2 == ["order.created"]
