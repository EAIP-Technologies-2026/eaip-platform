"""Tests for SnapshotService."""

from __future__ import annotations

import pytest

from eaip.eventsourcing.exceptions import SnapshotNotFoundError
from eaip.eventsourcing.snapshots import SnapshotService
from eaip.eventsourcing.store import EventStore


class TestSnapshotService:
    @pytest.fixture
    def store(self) -> EventStore:
        return EventStore()

    @pytest.fixture
    def service(self, store: EventStore) -> SnapshotService:
        return SnapshotService(store, snapshot_frequency=3)

    async def test_create_and_get_snapshot(self, service: SnapshotService) -> None:
        entry = await service.create_snapshot("order", "123", {"total": 100})
        assert entry.aggregate_type == "order"
        assert entry.aggregate_id == "123"
        assert entry.state == {"total": 100}
        assert entry.version == 0

        fetched = await service.get_snapshot("order", "123")
        assert fetched.state == {"total": 100}

    async def test_get_snapshot_not_found(self, service: SnapshotService) -> None:
        with pytest.raises(SnapshotNotFoundError):
            await service.get_snapshot("order", "nonexistent")

    async def test_delete_snapshot(self, service: SnapshotService) -> None:
        await service.create_snapshot("order", "123", {"total": 50})
        await service.delete_snapshot("order", "123")
        with pytest.raises(SnapshotNotFoundError):
            await service.get_snapshot("order", "123")

    async def test_delete_snapshot_not_found(self, service: SnapshotService) -> None:
        with pytest.raises(SnapshotNotFoundError):
            await service.delete_snapshot("order", "nonexistent")

    async def test_create_snapshot_version_increments(
        self, store: EventStore, service: SnapshotService
    ) -> None:
        store.append_event("order", "1", {"event_type": "order.created"})
        store.append_event("order", "1", {"event_type": "order.shipped"})
        entry = await service.create_snapshot("order", "1", {"state": "ok"})
        assert entry.version == 2

    async def test_should_create_snapshot_below_frequency(self, service: SnapshotService) -> None:
        result = await service.should_create_snapshot("order", "1")
        assert result is False

    async def test_should_create_snapshot_at_frequency(
        self, store: EventStore, service: SnapshotService
    ) -> None:
        for _i in range(3):
            store.append_event("order", "1", {"event_type": "order.updated"})
        result = await service.should_create_snapshot("order", "1")
        assert result is True

    async def test_should_create_snapshot_after_existing(
        self, store: EventStore, service: SnapshotService
    ) -> None:
        for _i in range(3):
            store.append_event("order", "1", {"event_type": "order.updated"})
        await service.create_snapshot("order", "1", {"state": "snap"})
        result = await service.should_create_snapshot("order", "1")
        assert result is False

        store.append_event("order", "1", {"event_type": "order.updated"})
        store.append_event("order", "1", {"event_type": "order.updated"})
        store.append_event("order", "1", {"event_type": "order.updated"})
        result = await service.should_create_snapshot("order", "1")
        assert result is True

    async def test_separate_aggregates(self, service: SnapshotService) -> None:
        await service.create_snapshot("order", "1", {"a": 1})
        await service.create_snapshot("invoice", "1", {"b": 2})
        s1 = await service.get_snapshot("order", "1")
        s2 = await service.get_snapshot("invoice", "1")
        assert s1.state == {"a": 1}
        assert s2.state == {"b": 2}
