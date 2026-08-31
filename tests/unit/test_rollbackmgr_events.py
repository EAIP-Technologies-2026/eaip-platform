"""Tests for rollbackmgr domain events."""

from __future__ import annotations

import pytest

from eaip.events.event import DomainEvent
from eaip.rollbackmgr.events import RollbackCompleted, RollbackFailed, RollbackStarted
from eaip.rollbackmgr.models import RollbackStrategy


class TestRollbackStarted:
    def test_defaults(self) -> None:
        e = RollbackStarted(
            execution_id="e1",
            deployment_id="d1",
            strategy=RollbackStrategy.IMMEDIATE,
            started_at="2025-01-01T00:00:00Z",
        )  # type: ignore[arg-type]
        assert e.event_type == "eaip.rollbackmgr.rollback.started"
        assert isinstance(e, DomainEvent)

    def test_with_values(self) -> None:
        e = RollbackStarted(
            execution_id="e1",
            deployment_id="d1",
            strategy=RollbackStrategy.GRADUAL,
            started_at="2025-01-01T00:00:00Z",
        )  # type: ignore[arg-type]
        assert e.strategy == RollbackStrategy.GRADUAL

    def test_frozen(self) -> None:
        e = RollbackStarted(
            execution_id="e1",
            deployment_id="d1",
            strategy=RollbackStrategy.IMMEDIATE,
            started_at="2025-01-01T00:00:00Z",
        )  # type: ignore[arg-type]
        with pytest.raises((ValueError, TypeError)):
            e.execution_id = "e2"


class TestRollbackCompleted:
    def test_defaults(self) -> None:
        e = RollbackCompleted(execution_id="e1", deployment_id="d1")
        assert e.event_type == "eaip.rollbackmgr.rollback.completed"
        assert e.output == ""

    def test_with_values(self) -> None:
        e = RollbackCompleted(
            execution_id="e1", deployment_id="d1", output="done", duration_seconds=30.5
        )
        assert e.output == "done"
        assert e.duration_seconds == 30.5


class TestRollbackFailed:
    def test_defaults(self) -> None:
        e = RollbackFailed(execution_id="e1", deployment_id="d1")
        assert e.event_type == "eaip.rollbackmgr.rollback.failed"
        assert e.error_message == ""

    def test_with_values(self) -> None:
        e = RollbackFailed(execution_id="e1", deployment_id="d1", error_message="timeout")
        assert e.error_message == "timeout"


class TestEventTypes:
    def test_all_have_unique_event_types(self) -> None:
        events = [RollbackStarted, RollbackCompleted, RollbackFailed]
        types = [e.event_type for e in events]
        assert len(types) == len(set(types))
