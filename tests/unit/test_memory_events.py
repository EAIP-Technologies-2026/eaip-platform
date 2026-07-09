"""Tests for Memory Engine domain events."""

from __future__ import annotations

from eaip.memory.events import (
    MemoryAccessTracked,
    MemoryArchived,
    MemoryConsolidated,
    MemoryCreated,
    MemoryDeleted,
    MemoryEngineEvent,
    MemoryExpired,
    MemoryRetrievalExecuted,
    MemoryRetrieved,
    MemorySearchExecuted,
    MemorySummarized,
    MemoryUpdated,
)
from eaip.memory.models import MemoryScope, MemoryType


class TestMemoryEngineEvent:
    def test_event_type(self) -> None:
        assert MemoryEngineEvent.event_type == "eaip.memory.event"


class TestMemoryCreated:
    def test_defaults(self) -> None:
        scope = MemoryScope(tenant_id="t1")
        ev = MemoryCreated(memory_id="m1", memory_type=MemoryType.WORKING, scope=scope, importance=0.5)
        assert ev.event_type == "eaip.memory.memory.created"
        assert ev.memory_id == "m1"
        assert ev.memory_type is MemoryType.WORKING
        assert ev.tags == ()

    def test_with_tags(self) -> None:
        scope = MemoryScope(tenant_id="t1")
        ev = MemoryCreated(memory_id="m1", memory_type=MemoryType.EPISODIC, scope=scope, importance=0.9, tags=("important",))
        assert "important" in ev.tags


class TestMemoryUpdated:
    def test_defaults(self) -> None:
        scope = MemoryScope(tenant_id="t1")
        ev = MemoryUpdated(memory_id="m1", scope=scope, version=2)
        assert ev.event_type == "eaip.memory.memory.updated"
        assert ev.version == 2
        assert ev.changes == ()

    def test_with_changes(self) -> None:
        scope = MemoryScope(tenant_id="t1")
        ev = MemoryUpdated(memory_id="m1", scope=scope, version=3, changes=("content", "tags"))
        assert "content" in ev.changes


class TestMemoryDeleted:
    def test_defaults(self) -> None:
        scope = MemoryScope(tenant_id="t1")
        ev = MemoryDeleted(memory_id="m1", scope=scope)
        assert ev.reason == ""
        assert ev.event_type == "eaip.memory.memory.deleted"

    def test_with_reason(self) -> None:
        scope = MemoryScope(tenant_id="t1")
        ev = MemoryDeleted(memory_id="m1", scope=scope, reason="user_requested")
        assert ev.reason == "user_requested"


class TestMemoryRetrieved:
    def test_event(self) -> None:
        scope = MemoryScope(tenant_id="t1")
        ev = MemoryRetrieved(memory_id="m1", scope=scope)
        assert ev.event_type == "eaip.memory.memory.retrieved"


class TestMemoryAccessTracked:
    def test_event(self) -> None:
        scope = MemoryScope(tenant_id="t1")
        ev = MemoryAccessTracked(memory_id="m1", scope=scope, access_count=5)
        assert ev.access_count == 5


class TestMemoryExpired:
    def test_event(self) -> None:
        scope = MemoryScope(tenant_id="t1")
        ev = MemoryExpired(memory_id="m1", scope=scope, memory_type=MemoryType.LONG_TERM)
        assert ev.event_type == "eaip.memory.memory.expired"
        assert ev.memory_type is MemoryType.LONG_TERM
        assert ev.reason == ""


class TestMemoryArchived:
    def test_event(self) -> None:
        scope = MemoryScope(tenant_id="t1")
        ev = MemoryArchived(memory_id="m1", scope=scope)
        assert ev.event_type == "eaip.memory.memory.archived"


class TestMemoryConsolidated:
    def test_defaults(self) -> None:
        ev = MemoryConsolidated()
        assert ev.event_type == "eaip.memory.memory.consolidated"
        assert ev.source_ids == ()
        assert ev.target_id == ""

    def test_with_values(self) -> None:
        ev = MemoryConsolidated(source_ids=("m1", "m2"), target_id="m3", consolidated_count=2)
        assert "m1" in ev.source_ids
        assert ev.target_id == "m3"


class TestMemorySummarized:
    def test_event(self) -> None:
        scope = MemoryScope(tenant_id="t1")
        ev = MemorySummarized(memory_id="m1", scope=scope)
        assert ev.event_type == "eaip.memory.memory.summarized"


class TestMemoryRetrievalExecuted:
    def test_event(self) -> None:
        ev = MemoryRetrievalExecuted(query="test query", result_count=3, duration_ms=1.5)
        assert ev.event_type == "eaip.memory.retrieval.executed"
        assert ev.query == "test query"
        assert ev.result_count == 3
        assert ev.duration_ms == 1.5
        assert ev.memory_type is None


class TestMemorySearchExecuted:
    def test_event(self) -> None:
        ev = MemorySearchExecuted(query="search", result_count=2, duration_ms=0.5)
        assert ev.event_type == "eaip.memory.search.executed"
        assert ev.filters == {}

    def test_with_filters(self) -> None:
        ev = MemorySearchExecuted(query="q", filters={"tag": "important"}, result_count=1, duration_ms=0.1)
        assert ev.filters["tag"] == "important"


class TestEventInheritance:
    def test_all_subclass_memory_engine_event(self) -> None:
        events = [
            MemoryAccessTracked,
            MemoryArchived,
            MemoryConsolidated,
            MemoryCreated,
            MemoryDeleted,
            MemoryExpired,
            MemoryRetrievalExecuted,
            MemoryRetrieved,
            MemorySearchExecuted,
            MemorySummarized,
            MemoryUpdated,
        ]
        for ev in events:
            assert issubclass(ev, MemoryEngineEvent), f"{ev.__name__} does not subclass MemoryEngineEvent"
