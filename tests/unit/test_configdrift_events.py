"""Tests for configdrift domain events."""

from __future__ import annotations

from eaip.configdrift.events import (
    DriftDetected,
    DriftResolved,
    SnapshotCaptured,
)
from eaip.events.event import DomainEvent


class TestSnapshotCaptured:
    def test_event_type(self) -> None:
        event = SnapshotCaptured(snapshot_id="s1", resource_id="res1")
        assert event.event_type == "eaip.configdrift.snapshot.captured"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = SnapshotCaptured(snapshot_id="s1", resource_id="res1")
        assert event.snapshot_id == "s1"
        assert event.resource_id == "res1"


class TestDriftDetected:
    def test_event_type(self) -> None:
        event = DriftDetected(
            report_id="dr1",
            resource_id="res1",
            baseline_id="s1",
            current_id="s2",
            differences_count=3,
            severity="warning",
        )
        assert event.event_type == "eaip.configdrift.drift.detected"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = DriftDetected(
            report_id="dr1",
            resource_id="res1",
            baseline_id="s1",
            current_id="s2",
            differences_count=3,
            severity="warning",
        )
        assert event.report_id == "dr1"
        assert event.resource_id == "res1"
        assert event.differences_count == 3
        assert event.severity == "warning"


class TestDriftResolved:
    def test_event_type(self) -> None:
        event = DriftResolved(report_id="dr1", resource_id="res1")
        assert event.event_type == "eaip.configdrift.drift.resolved"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = DriftResolved(report_id="dr1", resource_id="res1")
        assert event.report_id == "dr1"
        assert event.resource_id == "res1"


class TestAllEventsAreDomainEvents:
    def test_all_inherit_domain_event(self) -> None:
        assert issubclass(SnapshotCaptured, DomainEvent)
        assert issubclass(DriftDetected, DomainEvent)
        assert issubclass(DriftResolved, DomainEvent)
