"""Tests for :mod:`eaip.phealth.events`."""

from __future__ import annotations

import pytest

from eaip.phealth.events import (
    AlertResolved,
    AlertTriggered,
    MetricThresholdBreached,
    SnapshotTaken,
)


class TestSnapshotTaken:
    """Tests for :class:`eaip.phealth.events.SnapshotTaken`."""

    def test_create(self) -> None:
        """Test creating an event with required fields."""
        e = SnapshotTaken(snapshot_id="s1", component="api", status="healthy")
        assert e.event_type == "eaip.phealth.snapshot.taken"

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        e = SnapshotTaken(snapshot_id="s1", component="c", status="ok")
        with pytest.raises(ValueError):
            e.snapshot_id = "s2"


class TestMetricThresholdBreached:
    """Tests for :class:`eaip.phealth.events.MetricThresholdBreached`."""

    def test_create(self) -> None:
        """Test creating an event with required fields."""
        e = MetricThresholdBreached(metric_name="cpu", value=0.9, threshold=0.8)
        assert e.event_type == "eaip.phealth.metric.threshold_breached"


class TestAlertTriggered:
    """Tests for :class:`eaip.phealth.events.AlertTriggered`."""

    def test_create(self) -> None:
        """Test creating an event with required fields."""
        e = AlertTriggered(alert_id="a1", metric_name="cpu", component="api", severity="critical")
        assert e.event_type == "eaip.phealth.alert.triggered"


class TestAlertResolved:
    """Tests for :class:`eaip.phealth.events.AlertResolved`."""

    def test_create(self) -> None:
        """Test creating an event with required fields."""
        e = AlertResolved(alert_id="a1", metric_name="cpu", component="api")
        assert e.event_type == "eaip.phealth.alert.resolved"


def test_all_events_have_unique_types() -> None:
    """Test that all event types are unique."""
    types = [
        SnapshotTaken(snapshot_id="s1", component="c", status="ok").event_type,
        MetricThresholdBreached(metric_name="m", value=1, threshold=1).event_type,
        AlertTriggered(alert_id="a1", metric_name="m", component="c", severity="w").event_type,
        AlertResolved(alert_id="a1", metric_name="m", component="c").event_type,
    ]
    assert len(types) == len(set(types))
