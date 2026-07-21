from __future__ import annotations

from datetime import timedelta

import pytest

from eaip.observability.dashboards import DashboardService
from eaip.observability.exceptions import DashboardNotFoundError
from eaip.observability.models import (
    DashboardWidget,
    ObservabilityConfig,
    ObservabilityDashboard,
)


class TestDashboardService:
    def test_default_config(self) -> None:
        svc = DashboardService()
        assert svc.config.evaluation_interval_seconds == 60

    def test_custom_config(self) -> None:
        config = ObservabilityConfig(dashboard_refresh_default=300)
        svc = DashboardService(config=config)
        assert svc.config.dashboard_refresh_default == 300

    def test_create_and_get(self) -> None:
        svc = DashboardService()
        d = ObservabilityDashboard(id="d1", name="Test Dashboard")
        svc.create_dashboard(d)
        assert svc.get_dashboard("d1").name == "Test Dashboard"

    def test_get_not_found(self) -> None:
        svc = DashboardService()
        with pytest.raises(DashboardNotFoundError):
            svc.get_dashboard("nonexistent")

    def test_update_dashboard(self) -> None:
        svc = DashboardService()
        d = ObservabilityDashboard(id="d1", name="Old Name")
        svc.create_dashboard(d)
        svc.update_dashboard("d1", name="New Name")
        assert svc.get_dashboard("d1").name == "New Name"

    def test_delete_dashboard(self) -> None:
        svc = DashboardService()
        d = ObservabilityDashboard(id="d1", name="To Delete")
        svc.create_dashboard(d)
        svc.delete_dashboard("d1")
        with pytest.raises(DashboardNotFoundError):
            svc.get_dashboard("d1")

    def test_list_dashboards(self) -> None:
        svc = DashboardService()
        d1 = ObservabilityDashboard(id="d1", name="D1", enabled=True)
        d2 = ObservabilityDashboard(id="d2", name="D2", enabled=False)
        svc.create_dashboard(d1)
        svc.create_dashboard(d2)
        all_dashboards = svc.list_dashboards()
        assert len(all_dashboards) == 2
        enabled = svc.list_dashboards(enabled_only=True)
        assert len(enabled) == 1
        assert enabled[0].id == "d1"

    async def test_render_dashboard(self) -> None:
        svc = DashboardService()
        w = DashboardWidget(id="w1", type="timeseries", title="CPU", metric_sources=("cpu.usage",))
        d = ObservabilityDashboard(id="d1", name="Test", widgets=(w,))
        svc.create_dashboard(d)
        rendered = await svc.render_dashboard("d1")
        assert rendered["id"] == "d1"
        assert rendered["name"] == "Test"
        assert len(rendered["widgets"]) == 1
        assert rendered["widgets"][0]["id"] == "w1"
        assert rendered["widgets"][0]["type"] == "timeseries"

    async def test_render_widget(self) -> None:
        svc = DashboardService()
        w = DashboardWidget(id="w1", type="gauge", title="Memory", metric_sources=("memory.usage",))
        rendered = await svc.render_widget(w, timedelta(minutes=5))
        assert rendered["id"] == "w1"
        assert rendered["type"] == "gauge"
        assert len(rendered["series"]) == 1
        assert rendered["series"][0]["metric_source"] == "memory.usage"

    async def test_resolve_metric(self) -> None:
        svc = DashboardService()
        points = await svc.resolve_metric("cpu.usage", timedelta(minutes=1))
        assert len(points) > 0
        assert points[0].labels["source"] == "cpu.usage"
