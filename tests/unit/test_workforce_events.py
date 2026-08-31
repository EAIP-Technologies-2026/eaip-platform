"""Tests for workforce domain events."""

from __future__ import annotations

from eaip.events.event import DomainEvent
from eaip.workforce.events import (
    WorkerAssigned,
    WorkerAssignmentCompleted,
    WorkerAssignmentFailed,
    WorkerRegistered,
    WorkerScheduled,
    WorkerUnregistered,
)


class TestWorkerRegistered:
    def test_defaults(self) -> None:
        e = WorkerRegistered()
        assert e.event_type == "eaip.workforce.worker.registered"
        assert isinstance(e, DomainEvent)

    def test_with_values(self) -> None:
        e = WorkerRegistered(worker_id="w1", worker_name="Test", worker_type="agent", tags=("nlp",))
        assert e.worker_id == "w1"
        assert e.worker_name == "Test"
        assert e.worker_type == "agent"
        assert e.tags == ("nlp",)

    def test_frozen(self) -> None:
        e = WorkerRegistered(worker_id="w1")
        try:
            e.worker_id = "w2"
            raise AssertionError("should be frozen")
        except (ValueError, TypeError):
            pass


class TestWorkerUnregistered:
    def test_defaults(self) -> None:
        e = WorkerUnregistered()
        assert e.event_type == "eaip.workforce.worker.unregistered"

    def test_with_values(self) -> None:
        e = WorkerUnregistered(worker_id="w1", worker_name="Test", worker_type="agent")
        assert e.worker_id == "w1"
        assert e.worker_name == "Test"
        assert e.worker_type == "agent"


class TestWorkerAssigned:
    def test_defaults(self) -> None:
        e = WorkerAssigned()
        assert e.event_type == "eaip.workforce.worker.assigned"

    def test_with_values(self) -> None:
        e = WorkerAssigned(
            assignment_id="a1", worker_id="w1", task_description="Analyze", priority=50
        )
        assert e.assignment_id == "a1"
        assert e.priority == 50


class TestWorkerAssignmentCompleted:
    def test_defaults(self) -> None:
        e = WorkerAssignmentCompleted()
        assert e.event_type == "eaip.workforce.worker.assignment_completed"

    def test_with_values(self) -> None:
        e = WorkerAssignmentCompleted(
            assignment_id="a1", worker_id="w1", result="ok", duration_ms=150.0
        )
        assert e.result == "ok"
        assert e.duration_ms == 150.0


class TestWorkerAssignmentFailed:
    def test_defaults(self) -> None:
        e = WorkerAssignmentFailed()
        assert e.event_type == "eaip.workforce.worker.assignment_failed"

    def test_with_values(self) -> None:
        e = WorkerAssignmentFailed(assignment_id="a1", worker_id="w1", error="timeout")
        assert e.error == "timeout"


class TestWorkerScheduled:
    def test_defaults(self) -> None:
        e = WorkerScheduled()
        assert e.event_type == "eaip.workforce.worker.scheduled"
        assert not e.one_shot

    def test_recurring(self) -> None:
        e = WorkerScheduled(worker_id="w1", worker_name="Sync", schedule="0 * * * *")
        assert e.schedule == "0 * * * *"
        assert not e.one_shot

    def test_one_shot(self) -> None:
        e = WorkerScheduled(worker_id="w1", worker_name="Sync", schedule="delay:30s", one_shot=True)
        assert e.one_shot
