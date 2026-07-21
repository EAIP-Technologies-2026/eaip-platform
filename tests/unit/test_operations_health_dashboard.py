"""Tests for :mod:`eaip.operations.health_dashboard`."""

from __future__ import annotations

import pytest

from eaip.operations.health_dashboard import HealthDashboard
from eaip.operations.models import SystemHealthSnapshot


@pytest.fixture
def dashboard() -> HealthDashboard:
    return HealthDashboard()


class TestHealthDashboard:
    async def test_capture_snapshot(self, dashboard: HealthDashboard) -> None:
        snapshot = await dashboard.capture_snapshot()
        assert isinstance(snapshot, SystemHealthSnapshot)
        assert snapshot.id.startswith("snap-")
        assert snapshot.overall_status == "healthy"

    async def test_get_latest_snapshot(self, dashboard: HealthDashboard) -> None:
        await dashboard.capture_snapshot()
        snap2 = await dashboard.capture_snapshot()
        latest = await dashboard.get_latest_snapshot()
        assert latest is not None
        assert latest.id == snap2.id

    async def test_get_latest_snapshot_empty(self, dashboard: HealthDashboard) -> None:
        latest = await dashboard.get_latest_snapshot()
        assert latest is None

    async def test_get_snapshot_history(self, dashboard: HealthDashboard) -> None:
        for _ in range(5):
            await dashboard.capture_snapshot()
        history = await dashboard.get_snapshot_history(limit=3)
        assert len(history) == 3

    async def test_get_snapshot_history_limit_exceeds(self, dashboard: HealthDashboard) -> None:
        for _ in range(3):
            await dashboard.capture_snapshot()
        history = await dashboard.get_snapshot_history(limit=10)
        assert len(history) == 3

    async def test_get_snapshot_history_empty(self, dashboard: HealthDashboard) -> None:
        history = await dashboard.get_snapshot_history(limit=5)
        assert history == []

    async def test_get_component_health(self, dashboard: HealthDashboard) -> None:
        await dashboard.capture_snapshot()
        health = await dashboard.get_component_health("http")
        assert health["component"] == "http"
        assert health["status"] == "unknown"

    async def test_get_component_health_no_snapshots(self, dashboard: HealthDashboard) -> None:
        health = await dashboard.get_component_health("http")
        assert health["available"] is False

    async def test_get_system_metrics(self, dashboard: HealthDashboard) -> None:
        await dashboard.capture_snapshot()
        metrics = await dashboard.get_system_metrics()
        assert metrics == {}

    async def test_get_system_metrics_no_snapshots(self, dashboard: HealthDashboard) -> None:
        metrics = await dashboard.get_system_metrics()
        assert metrics == {}

    async def test_generate_health_report(self, dashboard: HealthDashboard) -> None:
        await dashboard.capture_snapshot()
        report = await dashboard.generate_health_report()
        assert report["status"] == "healthy"
        assert report["snapshots_available"] == 1

    async def test_generate_health_report_no_snapshots(self, dashboard: HealthDashboard) -> None:
        report = await dashboard.generate_health_report()
        assert report["status"] == "unknown"
        assert report["snapshots_available"] == 0

    async def test_multiple_snapshots_accumulate(self, dashboard: HealthDashboard) -> None:
        for _ in range(3):
            await dashboard.capture_snapshot()
        report = await dashboard.generate_health_report()
        assert report["snapshots_available"] == 3
