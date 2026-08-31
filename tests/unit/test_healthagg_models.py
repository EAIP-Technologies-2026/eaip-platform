"""Tests for health aggregation models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from eaip.health.checks import HealthStatus
from eaip.healthagg.models import (
    HealthAggregationConfig,
    HealthDependency,
    HealthSnapshot,
    HealthStatusPage,
    StatusPageStatus,
)


class TestHealthDependency:
    def test_minimal(self) -> None:
        d = HealthDependency(
            id="d1", source_component="db", target_component="api", dependency_type="hard"
        )
        assert d.id == "d1"
        assert d.dependency_type == "hard"
        assert d.optional is False
        assert d.metadata == {}

    def test_frozen(self) -> None:
        d = HealthDependency(
            id="d1", source_component="db", target_component="api", dependency_type="hard"
        )
        with pytest.raises(ValidationError):
            d.source_component = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            HealthDependency(
                id="d1",
                source_component="db",
                target_component="api",
                dependency_type="hard",
                unknown=True,
            )

    def test_all_dependency_types(self) -> None:
        for t in ("hard", "soft", "circuit"):
            d = HealthDependency(
                id=f"d_{t}", source_component="a", target_component="b", dependency_type=t
            )
            assert d.dependency_type == t

    def test_full(self) -> None:
        d = HealthDependency(
            id="d1",
            source_component="db",
            target_component="api",
            dependency_type="soft",
            optional=True,
            metadata={"latency": "10ms"},
        )
        assert d.optional is True
        assert d.metadata == {"latency": "10ms"}


class TestHealthStatusPage:
    def test_minimal(self) -> None:
        p = HealthStatusPage(id="p1", name="Main Status")
        assert p.description == ""
        assert p.components == ()
        assert p.layout == {}
        assert p.refresh_interval_seconds == 30
        assert p.public is False
        assert p.status == StatusPageStatus.ACTIVE
        assert p.metadata == {}

    def test_frozen(self) -> None:
        p = HealthStatusPage(id="p1", name="Main Status")
        with pytest.raises(ValidationError):
            p.name = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            HealthStatusPage(id="p1", name="Main Status", bad=True)

    def test_full(self) -> None:
        p = HealthStatusPage(
            id="p1",
            name="Full Page",
            description="Desc",
            components=("api", "db", "cache"),
            layout={"columns": 2},
            refresh_interval_seconds=60,
            public=True,
            status=StatusPageStatus.INACTIVE,
            metadata={"owner": "team-a"},
        )
        assert p.components == ("api", "db", "cache")
        assert p.layout == {"columns": 2}
        assert p.refresh_interval_seconds == 60
        assert p.public is True
        assert p.status == StatusPageStatus.INACTIVE
        assert p.metadata == {"owner": "team-a"}

    def test_status_enum(self) -> None:
        for s in ("active", "inactive", "archived"):
            p = HealthStatusPage(id="p1", name="Test", status=s)
            assert p.status.value == s


class TestHealthSnapshot:
    def test_minimal(self) -> None:
        s = HealthSnapshot(id="s1")
        assert s.component_statuses == {}
        assert s.overall_status == HealthStatus.HEALTHY
        assert s.dependencies_evaluated == 0
        assert s.duration_ms == 0.0
        assert s.metadata == {}

    def test_frozen(self) -> None:
        s = HealthSnapshot(id="s1")
        with pytest.raises(ValidationError):
            s.overall_status = HealthStatus.UNHEALTHY

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            HealthSnapshot(id="s1", bad=True)

    def test_full(self) -> None:
        ts = datetime.now(UTC)
        s = HealthSnapshot(
            id="s1",
            timestamp=ts,
            component_statuses={"api": HealthStatus.HEALTHY, "db": HealthStatus.DEGRADED},
            overall_status=HealthStatus.DEGRADED,
            dependencies_evaluated=5,
            duration_ms=120.5,
            metadata={"trigger": "scheduled"},
        )
        assert s.component_statuses == {"api": HealthStatus.HEALTHY, "db": HealthStatus.DEGRADED}
        assert s.overall_status == HealthStatus.DEGRADED
        assert s.dependencies_evaluated == 5
        assert s.duration_ms == 120.5
        assert s.timestamp == ts
        assert s.metadata == {"trigger": "scheduled"}


class TestHealthAggregationConfig:
    def test_defaults(self) -> None:
        c = HealthAggregationConfig()
        assert c.aggregation_interval_seconds == 60
        assert c.dependency_graph_enabled is True
        assert c.history_retention_days == 30
        assert c.max_snapshots == 10_000
        assert c.enable_status_pages is True

    def test_custom(self) -> None:
        c = HealthAggregationConfig(
            aggregation_interval_seconds=120,
            dependency_graph_enabled=False,
            history_retention_days=90,
            max_snapshots=5_000,
            enable_status_pages=False,
        )
        assert c.aggregation_interval_seconds == 120
        assert c.dependency_graph_enabled is False
        assert c.history_retention_days == 90
        assert c.max_snapshots == 5_000
        assert c.enable_status_pages is False

    def test_frozen(self) -> None:
        c = HealthAggregationConfig()
        with pytest.raises(ValidationError):
            c.max_snapshots = 1

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            HealthAggregationConfig(unknown=True)
