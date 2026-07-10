"""Tests for DashboardService."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from eaip.analytics.dashboard import DashboardService
from eaip.analytics.exceptions import DashboardNotFoundError
from eaip.analytics.models import DashboardDefinition, DashboardWidget, WidgetType


class TestDashboardService:
    @pytest.fixture
    def service(self) -> DashboardService:
        return DashboardService()

    class TestCreateDashboard:
        async def test_creates_dashboard(self, service: DashboardService) -> None:
            d = DashboardDefinition(id="d1", name="Main")
            result = await service.create_dashboard(d)
            assert result.id == "d1"
            assert result.name == "Main"

        async def test_overwrites_existing(self, service: DashboardService) -> None:
            d1 = DashboardDefinition(id="d1", name="Old")
            d2 = DashboardDefinition(id="d1", name="New")
            await service.create_dashboard(d1)
            await service.create_dashboard(d2)
            result = await service.get_dashboard("d1")
            assert result.name == "New"

    class TestGetDashboard:
        async def test_returns_dashboard(self, service: DashboardService) -> None:
            d = DashboardDefinition(id="d1", name="Main")
            await service.create_dashboard(d)
            result = await service.get_dashboard("d1")
            assert result.id == "d1"

        async def test_raises_on_missing(self, service: DashboardService) -> None:
            with pytest.raises(DashboardNotFoundError):
                await service.get_dashboard("nonexistent")

    class TestUpdateDashboard:
        async def test_updates_name(self, service: DashboardService) -> None:
            d = DashboardDefinition(id="d1", name="Main")
            await service.create_dashboard(d)
            updated = await service.update_dashboard("d1", {"name": "Updated"})
            assert updated.name == "Updated"

        async def test_updates_widgets(self, service: DashboardService) -> None:
            w = DashboardWidget(id="w1", type=WidgetType.GAUGE)
            d = DashboardDefinition(id="d1", name="Main")
            await service.create_dashboard(d)
            updated = await service.update_dashboard("d1", {"widgets": (w,)})
            assert len(updated.widgets) == 1

        async def test_raises_on_missing(self, service: DashboardService) -> None:
            with pytest.raises(DashboardNotFoundError):
                await service.update_dashboard("nonexistent", {"name": "X"})

    class TestDeleteDashboard:
        async def test_deletes_dashboard(self, service: DashboardService) -> None:
            d = DashboardDefinition(id="d1", name="Main")
            await service.create_dashboard(d)
            await service.delete_dashboard("d1")
            assert len(await service.list_dashboards()) == 0

        async def test_raises_on_missing(self, service: DashboardService) -> None:
            with pytest.raises(DashboardNotFoundError):
                await service.delete_dashboard("nonexistent")

    class TestListDashboards:
        async def test_empty(self, service: DashboardService) -> None:
            assert await service.list_dashboards() == []

        async def test_returns_all(self, service: DashboardService) -> None:
            await service.create_dashboard(DashboardDefinition(id="d1", name="A"))
            await service.create_dashboard(DashboardDefinition(id="d2", name="B"))
            result = await service.list_dashboards()
            assert len(result) == 2

    class TestRenderWidget:
        async def test_renders_widget(self, service: DashboardService) -> None:
            w = DashboardWidget(id="w1", type=WidgetType.TIMESERIES, metric_ids=("m1",), title="Test")
            d = DashboardDefinition(id="d1", name="Main", widgets=(w,))
            await service.create_dashboard(d)
            now = datetime.now(timezone.utc)
            result = await service.render_widget("w1", (now - timedelta(hours=1), now))
            assert result["widget_id"] == "w1"
            assert result["type"] == "timeseries"

        async def test_raises_on_missing_widget(self, service: DashboardService) -> None:
            now = datetime.now(timezone.utc)
            with pytest.raises(DashboardNotFoundError):
                await service.render_widget("unknown", (now, now))

    class TestRenderDashboard:
        async def test_renders_full_dashboard(self, service: DashboardService) -> None:
            w1 = DashboardWidget(id="w1", type=WidgetType.TIMESERIES, metric_ids=("m1",), title="Chart")
            d = DashboardDefinition(id="d1", name="Main", widgets=(w1,))
            await service.create_dashboard(d)
            now = datetime.now(timezone.utc)
            result = await service.render_dashboard("d1", (now - timedelta(hours=1), now))
            assert result["dashboard_id"] == "d1"
            assert len(result["widgets"]) == 1

        async def test_raises_on_missing_dashboard(self, service: DashboardService) -> None:
            now = datetime.now(timezone.utc)
            with pytest.raises(DashboardNotFoundError):
                await service.render_dashboard("unknown", (now, now))

    class TestConstruction:
        def test_default_construction(self) -> None:
            svc = DashboardService()
            assert isinstance(svc, DashboardService)
