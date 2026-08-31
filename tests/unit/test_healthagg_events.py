"""Tests for health aggregation domain events."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.health.checks import HealthStatus
from eaip.healthagg.events import (
    ComponentStatusChanged,
    DependencyImpactDetected,
    HealthCheckCompleted,
    HealthDegraded,
    HealthRestored,
    SnapshotCaptured,
    StatusPageCreated,
    StatusPageUpdated,
)


class TestHealthCheckCompleted:
    def test_minimal(self) -> None:
        e = HealthCheckCompleted(component="api", status=HealthStatus.HEALTHY, duration_ms=10.5)
        assert e.event_type == "eaip.healthagg.check_completed"
        assert e.component == "api"
        assert e.duration_ms == 10.5

    def test_frozen(self) -> None:
        e = HealthCheckCompleted(component="api", status=HealthStatus.HEALTHY, duration_ms=10.5)
        with pytest.raises(ValidationError):
            e.component = "changed"


class TestComponentStatusChanged:
    def test_minimal(self) -> None:
        e = ComponentStatusChanged(
            component="api",
            previous_status=HealthStatus.HEALTHY,
            new_status=HealthStatus.UNHEALTHY,
        )
        assert e.event_type == "eaip.healthagg.component_status_changed"
        assert e.previous_status == HealthStatus.HEALTHY
        assert e.new_status == HealthStatus.UNHEALTHY


class TestDependencyImpactDetected:
    def test_minimal(self) -> None:
        e = DependencyImpactDetected(source_component="db", affected_components=("api", "web"))
        assert e.event_type == "eaip.healthagg.dependency_impact_detected"
        assert e.affected_components == ("api", "web")


class TestStatusPageCreated:
    def test_minimal(self) -> None:
        e = StatusPageCreated(page_id="p1", page_name="Main Status")
        assert e.event_type == "eaip.healthagg.status_page_created"
        assert e.page_id == "p1"
        assert e.page_name == "Main Status"


class TestStatusPageUpdated:
    def test_minimal(self) -> None:
        e = StatusPageUpdated(page_id="p1", page_name="Updated Status")
        assert e.event_type == "eaip.healthagg.status_page_updated"
        assert e.page_id == "p1"


class TestSnapshotCaptured:
    def test_minimal(self) -> None:
        e = SnapshotCaptured(
            snapshot_id="s1", overall_status=HealthStatus.DEGRADED, component_count=5
        )
        assert e.event_type == "eaip.healthagg.snapshot_captured"
        assert e.snapshot_id == "s1"
        assert e.component_count == 5


class TestHealthDegraded:
    def test_minimal(self) -> None:
        e = HealthDegraded(
            component="api",
            previous_status=HealthStatus.HEALTHY,
            current_status=HealthStatus.UNHEALTHY,
        )
        assert e.event_type == "eaip.healthagg.health_degraded"
        assert e.current_status == HealthStatus.UNHEALTHY


class TestHealthRestored:
    def test_minimal(self) -> None:
        e = HealthRestored(
            component="api",
            previous_status=HealthStatus.UNHEALTHY,
            current_status=HealthStatus.HEALTHY,
        )
        assert e.event_type == "eaip.healthagg.health_restored"
        assert e.current_status == HealthStatus.HEALTHY


class TestEventFrozen:
    @pytest.mark.parametrize(
        "event_cls, kwargs",
        [
            (
                HealthCheckCompleted,
                {"component": "x", "status": HealthStatus.HEALTHY, "duration_ms": 1.0},
            ),
            (
                ComponentStatusChanged,
                {
                    "component": "x",
                    "previous_status": HealthStatus.HEALTHY,
                    "new_status": HealthStatus.UNHEALTHY,
                },
            ),
            (DependencyImpactDetected, {"source_component": "a", "affected_components": ("b",)}),
            (StatusPageCreated, {"page_id": "p1", "page_name": "Test"}),
            (StatusPageUpdated, {"page_id": "p1", "page_name": "Test"}),
            (
                SnapshotCaptured,
                {"snapshot_id": "s1", "overall_status": HealthStatus.HEALTHY, "component_count": 1},
            ),
            (
                HealthDegraded,
                {
                    "component": "x",
                    "previous_status": HealthStatus.HEALTHY,
                    "current_status": HealthStatus.UNHEALTHY,
                },
            ),
            (
                HealthRestored,
                {
                    "component": "x",
                    "previous_status": HealthStatus.UNHEALTHY,
                    "current_status": HealthStatus.HEALTHY,
                },
            ),
        ],
    )
    def test_all_events_frozen(self, event_cls: type, kwargs: dict) -> None:
        e = event_cls(**kwargs)
        for field in kwargs:
            with pytest.raises(ValidationError):
                setattr(e, field, "changed")
