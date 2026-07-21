"""Tests for event sourcing domain events."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.eventsourcing.events import (
    EventStored,
    ProjectionBuilt,
    ProjectionRebuilt,
    ProjectionRegistered,
    ReplayCompleted,
    ReplayStarted,
    SnapshotCreated,
)


class TestEventStored:
    def test_minimal(self) -> None:
        e = EventStored(
            aggregate_type="order", aggregate_id="123", event_type_name="order.created", version=1
        )
        assert e.event_type == "eventsourcing.event.stored"
        assert e.version == 1

    def test_frozen(self) -> None:
        e = EventStored(
            aggregate_type="order", aggregate_id="123", event_type_name="order.created", version=1
        )
        with pytest.raises(ValidationError):
            e.aggregate_type = "changed"


class TestProjectionRegistered:
    def test_minimal(self) -> None:
        e = ProjectionRegistered(
            projection_id="p1", projection_name="OrderCount", aggregate_types=("order",)
        )
        assert e.event_type == "eventsourcing.projection.registered"
        assert e.aggregate_types == ("order",)

    def test_empty_types(self) -> None:
        e = ProjectionRegistered(projection_id="p1", projection_name="Empty")
        assert e.aggregate_types == ()


class TestProjectionBuilt:
    def test_minimal(self) -> None:
        e = ProjectionBuilt(projection_id="p1", projection_name="OrderCount", events_processed=42)
        assert e.event_type == "eventsourcing.projection.built"
        assert e.events_processed == 42


class TestProjectionRebuilt:
    def test_minimal(self) -> None:
        e = ProjectionRebuilt(
            projection_id="p1", projection_name="OrderCount", events_processed=100
        )
        assert e.event_type == "eventsourcing.projection.rebuilt"
        assert e.events_processed == 100


class TestReplayStarted:
    def test_minimal(self) -> None:
        e = ReplayStarted()
        assert e.event_type == "eventsourcing.replay.started"
        assert e.aggregate_type is None

    def test_with_aggregate(self) -> None:
        e = ReplayStarted(aggregate_type="order", aggregate_id="123")
        assert e.aggregate_type == "order"
        assert e.aggregate_id == "123"

    def test_with_range(self) -> None:
        e = ReplayStarted(range_start=10, range_end=50)
        assert e.range_start == 10
        assert e.range_end == 50


class TestReplayCompleted:
    def test_minimal(self) -> None:
        e = ReplayCompleted(events_processed=10, duration_seconds=1.5)
        assert e.event_type == "eventsourcing.replay.completed"
        assert e.events_processed == 10
        assert e.duration_seconds == 1.5


class TestSnapshotCreated:
    def test_minimal(self) -> None:
        e = SnapshotCreated(aggregate_type="order", aggregate_id="123", version=5)
        assert e.event_type == "eventsourcing.snapshot.created"
        assert e.version == 5

    def test_frozen(self) -> None:
        e = SnapshotCreated(aggregate_type="order", aggregate_id="123", version=5)
        with pytest.raises(ValidationError):
            e.version = 6
