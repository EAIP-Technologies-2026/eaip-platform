from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from eaip.compliance.exceptions import ComplianceError
from eaip.compliance.remediation import RemediationTracker


class TestRemediationTracker:
    @pytest.fixture
    def tracker(self) -> RemediationTracker:
        return RemediationTracker()

    @pytest.mark.asyncio
    async def test_create_item(self, tracker: RemediationTracker) -> None:
        item = await tracker.create_item("c1", "Enable encryption at rest")
        assert item.control_id == "c1"
        assert item.description == "Enable encryption at rest"
        assert item.status == "open"
        assert item.resolved_at is None
        assert item.assigned_to is None

    @pytest.mark.asyncio
    async def test_create_item_with_assignment(self, tracker: RemediationTracker) -> None:
        item = await tracker.create_item("c1", "Fix access control", assigned_to="alice")
        assert item.assigned_to == "alice"

    @pytest.mark.asyncio
    async def test_create_item_with_event_bus(self, tracker: RemediationTracker) -> None:
        event_bus = MagicMock()
        event_bus.publish = AsyncMock()
        await tracker.create_item("c1", "Fix it", event_bus=event_bus)
        event_bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_resolve_item(self, tracker: RemediationTracker) -> None:
        item = await tracker.create_item("c1", "Fix it")
        resolved = await tracker.resolve_item(item.item_id)
        assert resolved.status == "resolved"
        assert resolved.resolved_at is not None

    @pytest.mark.asyncio
    async def test_resolve_item_not_found(self, tracker: RemediationTracker) -> None:
        with pytest.raises(ComplianceError):
            await tracker.resolve_item("nonexistent")

    @pytest.mark.asyncio
    async def test_resolve_item_with_event_bus(self, tracker: RemediationTracker) -> None:
        event_bus = MagicMock()
        event_bus.publish = AsyncMock()
        item = await tracker.create_item("c1", "Fix it")
        await tracker.resolve_item(item.item_id, event_bus=event_bus)
        event_bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_item_found(self, tracker: RemediationTracker) -> None:
        item = await tracker.create_item("c1", "Fix it")
        found = tracker.get_item(item.item_id)
        assert found is not None
        assert found.item_id == item.item_id

    @pytest.mark.asyncio
    async def test_get_item_not_found(self, tracker: RemediationTracker) -> None:
        assert tracker.get_item("nonexistent") is None

    @pytest.mark.asyncio
    async def test_list_items(self, tracker: RemediationTracker) -> None:
        await tracker.create_item("c1", "Fix A")
        await tracker.create_item("c2", "Fix B")
        items = tracker.list_items()
        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_list_items_filter_by_status(self, tracker: RemediationTracker) -> None:
        await tracker.create_item("c1", "Fix A")
        item2 = await tracker.create_item("c2", "Fix B")
        await tracker.resolve_item(item2.item_id)
        open_items = tracker.list_items("open")
        assert len(open_items) == 1
        assert open_items[0].status == "open"
        resolved_items = tracker.list_items("resolved")
        assert len(resolved_items) == 1
        assert resolved_items[0].status == "resolved"

    @pytest.mark.asyncio
    async def test_count_by_status(self, tracker: RemediationTracker) -> None:
        item1 = await tracker.create_item("c1", "Fix A")
        await tracker.create_item("c2", "Fix B")
        await tracker.resolve_item(item1.item_id)
        counts = tracker.count_by_status()
        assert counts["open"] == 1
        assert counts["resolved"] == 1

    def test_clear(self, tracker: RemediationTracker) -> None:
        tracker.clear()
        assert tracker.list_items() == ()
