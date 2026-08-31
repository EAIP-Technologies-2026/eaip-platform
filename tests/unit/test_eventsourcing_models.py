"""Tests for event sourcing models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from eaip.eventsourcing.models import (
    EventSourcingConfig,
    EventStream,
    Projection,
    ProjectionConfig,
    ProjectionStatus,
    StoredEvent,
)


class TestStoredEvent:
    def test_minimal(self) -> None:
        e = StoredEvent(
            id="e1", aggregate_type="order", aggregate_id="123", event_type="order.created"
        )
        assert e.event_data == {}
        assert e.metadata == {}
        assert e.version == 1
        assert e.correlation_id == ""
        assert e.causation_id == ""

    def test_frozen(self) -> None:
        e = StoredEvent(
            id="e1", aggregate_type="order", aggregate_id="123", event_type="order.created"
        )
        with pytest.raises(ValidationError):
            e.event_type = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            StoredEvent(
                id="e1", aggregate_type="order", aggregate_id="123", event_type="test", unknown=True
            )

    def test_full(self) -> None:
        ts = datetime.now(UTC)
        e = StoredEvent(
            id="e1",
            aggregate_type="order",
            aggregate_id="123",
            event_type="order.created",
            event_data={"amount": 100},
            metadata={"ip": "10.0.0.1"},
            version=5,
            timestamp=ts,
            correlation_id="corr-1",
            causation_id="caus-1",
        )
        assert e.event_data == {"amount": 100}
        assert e.metadata == {"ip": "10.0.0.1"}
        assert e.version == 5
        assert e.timestamp == ts
        assert e.correlation_id == "corr-1"
        assert e.causation_id == "caus-1"


class TestEventStream:
    def test_minimal(self) -> None:
        s = EventStream(aggregate_type="order", aggregate_id="123")
        assert s.events == ()
        assert s.current_version == 0

    def test_with_events(self) -> None:
        e1 = StoredEvent(
            id="e1", aggregate_type="order", aggregate_id="123", event_type="order.created"
        )
        e2 = StoredEvent(
            id="e2", aggregate_type="order", aggregate_id="123", event_type="order.shipped"
        )
        s = EventStream(
            aggregate_type="order", aggregate_id="123", events=(e1, e2), current_version=2
        )
        assert len(s.events) == 2
        assert s.current_version == 2

    def test_frozen(self) -> None:
        s = EventStream(aggregate_type="order", aggregate_id="123")
        with pytest.raises(ValidationError):
            s.aggregate_type = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            EventStream(aggregate_type="order", aggregate_id="123", bad=True)


class TestProjection:
    def test_minimal(self) -> None:
        p = Projection(id="p1", name="OrderSummary")
        assert p.aggregate_types == ()
        assert p.status == ProjectionStatus.ACTIVE
        assert p.last_processed_event_id == ""
        assert p.last_processed_at is None
        assert p.state == {}

    def test_frozen(self) -> None:
        p = Projection(id="p1", name="OrderSummary")
        with pytest.raises(ValidationError):
            p.name = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            Projection(id="p1", name="Test", bad=True)

    def test_full(self) -> None:
        ts = datetime.now(UTC)
        p = Projection(
            id="p1",
            name="OrderSummary",
            aggregate_types=("order",),
            handler_type="count",
            status=ProjectionStatus.PAUSED,
            last_processed_event_id="e100",
            last_processed_at=ts,
            state={"count": 42},
            metadata={"owner": "team-a"},
        )
        assert p.aggregate_types == ("order",)
        assert p.handler_type == "count"
        assert p.status == ProjectionStatus.PAUSED
        assert p.last_processed_event_id == "e100"
        assert p.last_processed_at == ts
        assert p.state == {"count": 42}
        assert p.metadata == {"owner": "team-a"}

    def test_all_statuses(self) -> None:
        for s in ProjectionStatus:
            p = Projection(id="p1", name="Test", status=s)
            assert p.status == s


class TestProjectionConfig:
    def test_defaults(self) -> None:
        c = ProjectionConfig()
        assert c.batch_size == 100
        assert c.max_retries == 3
        assert c.retry_delay_seconds == 1.0
        assert c.enable_checkpointing is True
        assert c.checkpoint_interval == 10

    def test_custom(self) -> None:
        c = ProjectionConfig(
            batch_size=50,
            max_retries=5,
            retry_delay_seconds=2.5,
            enable_checkpointing=False,
            checkpoint_interval=20,
        )
        assert c.batch_size == 50
        assert c.max_retries == 5
        assert c.retry_delay_seconds == 2.5
        assert c.enable_checkpointing is False
        assert c.checkpoint_interval == 20

    def test_frozen(self) -> None:
        c = ProjectionConfig()
        with pytest.raises(ValidationError):
            c.batch_size = 200

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            ProjectionConfig(unknown=True)


class TestEventSourcingConfig:
    def test_defaults(self) -> None:
        c = EventSourcingConfig()
        assert c.max_events_per_aggregate == 10_000
        assert c.enable_snapshots is True
        assert c.snapshot_frequency == 100
        assert c.retention_days == 90
        assert c.archive_enabled is False

    def test_custom(self) -> None:
        c = EventSourcingConfig(
            max_events_per_aggregate=5_000,
            enable_snapshots=False,
            snapshot_frequency=50,
            retention_days=30,
            archive_enabled=True,
        )
        assert c.max_events_per_aggregate == 5_000
        assert c.enable_snapshots is False
        assert c.snapshot_frequency == 50
        assert c.retention_days == 30
        assert c.archive_enabled is True

    def test_frozen(self) -> None:
        c = EventSourcingConfig()
        with pytest.raises(ValidationError):
            c.retention_days = 60

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            EventSourcingConfig(unknown=True)
