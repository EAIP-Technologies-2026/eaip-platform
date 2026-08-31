"""Tests for Enterprise Brain domain events."""

from __future__ import annotations

from eaip.brain.events import (
    BrainAccessDenied,
    BrainContextBuilt,
    BrainEvent,
    BrainKnowledgeRetrieved,
    BrainMemoryRetrieved,
    BrainQueryExecuted,
    BrainSyncCompleted,
    DepartmentBrainQueryExecuted,
)


class TestBrainEvent:
    def test_event_type(self) -> None:
        assert BrainEvent.event_type == "eaip.brain.event"


class TestBrainQueryExecuted:
    def test_defaults(self) -> None:
        ev = BrainQueryExecuted(query="test query", source_count=5, duration_ms=100.0)
        assert ev.event_type == "eaip.brain.query.executed"
        assert ev.query == "test query"
        assert ev.source_count == 5
        assert ev.duration_ms == 100.0
        assert ev.confidence == 0.0

    def test_with_confidence(self) -> None:
        ev = BrainQueryExecuted(query="q1", source_count=3, duration_ms=50.0, confidence=0.85)
        assert ev.confidence == 0.85


class TestBrainKnowledgeRetrieved:
    def test_defaults(self) -> None:
        ev = BrainKnowledgeRetrieved(query="knowledge query", result_count=10, duration_ms=200.0)
        assert ev.event_type == "eaip.brain.knowledge.retrieved"
        assert ev.collections == ()
        assert ev.result_count == 10

    def test_with_collections(self) -> None:
        ev = BrainKnowledgeRetrieved(
            query="q1",
            collections=("docs", "wiki"),
            result_count=5,
            duration_ms=150.0,
        )
        assert "docs" in ev.collections


class TestBrainMemoryRetrieved:
    def test_event(self) -> None:
        ev = BrainMemoryRetrieved(query="memory query", result_count=3, duration_ms=75.0)
        assert ev.event_type == "eaip.brain.memory.retrieved"
        assert ev.query == "memory query"
        assert ev.result_count == 3
        assert ev.duration_ms == 75.0


class TestBrainContextBuilt:
    def test_defaults(self) -> None:
        ev = BrainContextBuilt(
            query="ctx query", document_count=2, total_tokens=500, duration_ms=30.0
        )
        assert ev.event_type == "eaip.brain.context.built"
        assert ev.document_count == 2
        assert ev.total_tokens == 500
        assert ev.duration_ms == 30.0


class TestDepartmentBrainQueryExecuted:
    def test_defaults(self) -> None:
        ev = DepartmentBrainQueryExecuted(
            department_id="eng",
            query="test",
            source_count=3,
            duration_ms=50.0,
        )
        assert ev.event_type == "eaip.brain.department.query.executed"
        assert ev.department_id == "eng"
        assert ev.query == "test"
        assert ev.source_count == 3
        assert ev.duration_ms == 50.0
        assert ev.confidence == 0.0

    def test_with_confidence(self) -> None:
        ev = DepartmentBrainQueryExecuted(
            department_id="hr",
            query="q1",
            source_count=1,
            duration_ms=10.0,
            confidence=0.9,
        )
        assert ev.confidence == 0.9


class TestBrainAccessDenied:
    def test_defaults(self) -> None:
        ev = BrainAccessDenied(
            subject_id="alice",
            brain_type="enterprise",
            action="query",
        )
        assert ev.event_type == "eaip.brain.access.denied"
        assert ev.subject_id == "alice"
        assert ev.brain_type == "enterprise"
        assert ev.department_id == ""
        assert ev.reason == ""

    def test_with_department(self) -> None:
        ev = BrainAccessDenied(
            subject_id="bob",
            brain_type="department",
            department_id="eng",
            action="query",
            reason="Not authorized",
        )
        assert ev.department_id == "eng"
        assert ev.reason == "Not authorized"


class TestBrainSyncCompleted:
    def test_defaults(self) -> None:
        ev = BrainSyncCompleted(department_id="eng", synced_count=42, duration_ms=100.0)
        assert ev.event_type == "eaip.brain.sync.completed"
        assert ev.department_id == "eng"
        assert ev.synced_count == 42
        assert ev.duration_ms == 100.0


class TestEventInheritance:
    def test_all_subclass_brain_event(self) -> None:
        events = [
            BrainQueryExecuted,
            BrainKnowledgeRetrieved,
            BrainMemoryRetrieved,
            BrainContextBuilt,
            DepartmentBrainQueryExecuted,
            BrainAccessDenied,
            BrainSyncCompleted,
        ]
        for ev in events:
            assert issubclass(ev, BrainEvent), f"{ev.__name__} does not subclass BrainEvent"
