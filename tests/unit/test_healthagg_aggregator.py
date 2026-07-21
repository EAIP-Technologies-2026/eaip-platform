"""Tests for HealthAggregator."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from eaip.health.checks import HealthReport, HealthStatus
from eaip.healthagg.aggregator import HealthAggregator
from eaip.healthagg.exceptions import ComponentNotFoundError
from eaip.healthagg.models import HealthAggregationConfig


class _MockCheck:
    def __init__(self, name: str, status: HealthStatus = HealthStatus.HEALTHY) -> None:
        self.name = name
        self._status = status

    async def check(self) -> HealthReport:
        return HealthReport(component=self.name, status=self._status)


class TestHealthAggregator:
    def test_register_component(self) -> None:
        agg = HealthAggregator()
        agg.register_component("api")
        assert "api" not in agg._checks
        agg.register_component("db", _MockCheck("db"))
        assert "db" in agg._checks

    def test_unregister_component(self) -> None:
        agg = HealthAggregator()
        agg.register_component("db", _MockCheck("db"))
        assert agg.unregister_component("db") is True
        assert agg.unregister_component("nonexistent") is False

    def test_unregister_clears_previous_status(self) -> None:
        agg = HealthAggregator()
        agg.register_component("db", _MockCheck("db"))
        agg._previous_statuses["db"] = HealthStatus.HEALTHY
        agg.unregister_component("db")
        assert "db" not in agg._previous_statuses

    async def test_aggregate_no_checks(self) -> None:
        agg = HealthAggregator()
        report = await agg.aggregate()
        assert report.status == HealthStatus.HEALTHY
        assert report.message == "no components registered"

    async def test_aggregate_all_healthy(self) -> None:
        agg = HealthAggregator()
        agg.register_component("api", _MockCheck("api", HealthStatus.HEALTHY))
        agg.register_component("db", _MockCheck("db", HealthStatus.HEALTHY))
        report = await agg.aggregate()
        assert report.status == HealthStatus.HEALTHY
        assert len(report.children) == 2

    async def test_aggregate_degraded(self) -> None:
        agg = HealthAggregator()
        agg.register_component("api", _MockCheck("api", HealthStatus.HEALTHY))
        agg.register_component("db", _MockCheck("db", HealthStatus.DEGRADED))
        report = await agg.aggregate()
        assert report.status == HealthStatus.DEGRADED

    async def test_aggregate_unhealthy(self) -> None:
        agg = HealthAggregator()
        agg.register_component("api", _MockCheck("api", HealthStatus.UNHEALTHY))
        report = await agg.aggregate()
        assert report.status == HealthStatus.UNHEALTHY

    async def test_aggregate_check_raises_exception(self) -> None:
        class _FailingCheck:
            name = "failing"

            async def check(self) -> HealthReport:
                raise RuntimeError("boom")

        agg = HealthAggregator()
        agg.register_component("failing", _FailingCheck())
        report = await agg.aggregate()
        assert report.status == HealthStatus.UNHEALTHY
        assert "boom" in report.children[0].message

    async def test_get_component_health(self) -> None:
        agg = HealthAggregator()
        agg.register_component("api", _MockCheck("api", HealthStatus.HEALTHY))
        report = await agg.get_component_health("api")
        assert report.status == HealthStatus.HEALTHY

    async def test_get_component_health_not_found(self) -> None:
        agg = HealthAggregator()
        with pytest.raises(ComponentNotFoundError):
            await agg.get_component_health("nonexistent")

    async def test_get_all_components(self) -> None:
        agg = HealthAggregator()
        agg.register_component("api", _MockCheck("api", HealthStatus.HEALTHY))
        agg.register_component("db", _MockCheck("db", HealthStatus.DEGRADED))
        all_comps = await agg.get_all_components()
        assert all_comps == {"api": HealthStatus.HEALTHY, "db": HealthStatus.DEGRADED}

    async def test_capture_snapshot(self) -> None:
        agg = HealthAggregator()
        agg.register_component("api", _MockCheck("api", HealthStatus.HEALTHY))
        snap = await agg.capture_snapshot()
        assert snap.id is not None
        assert snap.overall_status == HealthStatus.HEALTHY
        assert snap.component_statuses == {"api": HealthStatus.HEALTHY}
        assert snap.duration_ms >= 0

    async def test_capture_snapshot_overall_degraded(self) -> None:
        agg = HealthAggregator()
        agg.register_component("api", _MockCheck("api", HealthStatus.DEGRADED))
        snap = await agg.capture_snapshot()
        assert snap.overall_status == HealthStatus.DEGRADED

    async def test_get_snapshots(self) -> None:
        agg = HealthAggregator()
        agg.register_component("api", _MockCheck("api", HealthStatus.HEALTHY))
        await agg.capture_snapshot()
        s2 = await agg.capture_snapshot()
        snaps = await agg.get_snapshots(limit=1)
        assert len(snaps) == 1
        assert snaps[0].id == s2.id

    async def test_snapshots_trim(self) -> None:
        agg = HealthAggregator(config=HealthAggregationConfig(max_snapshots=3))
        agg.register_component("api", _MockCheck("api", HealthStatus.HEALTHY))
        ids = []
        for _ in range(5):
            s = await agg.capture_snapshot()
            ids.append(s.id)
        snaps = await agg.get_snapshots(limit=10)
        assert len(snaps) == 3
        assert snaps[0].id == ids[2]

    def test_config_property(self) -> None:
        config = HealthAggregationConfig(aggregation_interval_seconds=120)
        agg = HealthAggregator(config=config)
        assert agg.config.aggregation_interval_seconds == 120

    def test_dependency_graph_property(self) -> None:
        agg = HealthAggregator()
        assert agg.dependency_graph is not None

    def test_publishes_events(self) -> None:
        bus = MagicMock()
        agg = HealthAggregator(event_bus=bus)
        agg.register_component("api", _MockCheck("api", HealthStatus.HEALTHY))
        bus.publish.assert_not_called()
