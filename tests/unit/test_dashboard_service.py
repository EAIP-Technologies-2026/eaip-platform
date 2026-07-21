"""Tests for DashboardBuilder service."""

from __future__ import annotations

import pytest

from eaip.dashboard.builder import DashboardBuilder
from eaip.dashboard.exceptions import DashboardNotFoundError
from eaip.dashboard.models import DashboardConfig, WidgetDefinition, WidgetType


class TestDashboardBuilder:
    @pytest.fixture
    def builder(self) -> DashboardBuilder:
        return DashboardBuilder()

    @pytest.fixture
    def sample_widget(self) -> WidgetDefinition:
        return WidgetDefinition(
            id="w1",
            widget_type=WidgetType.CHART,
            title="CPU Usage",
            config={"metric": "cpu_percent"},
        )

    class TestCreateDashboard:
        async def test_create_dashboard(self, builder: DashboardBuilder) -> None:
            dashboard = await builder.create_dashboard(dashboard_id="d1", name="Infra Overview")
            assert dashboard.id == "d1"
            assert dashboard.name == "Infra Overview"

        async def test_create_dashboard_with_config(self, builder: DashboardBuilder) -> None:
            config = DashboardConfig(theme="dark", refresh_interval_seconds=60)
            dashboard = await builder.create_dashboard(
                dashboard_id="d2", name="Dark Dashboard", config=config
            )
            assert dashboard.config.theme == "dark"
            assert dashboard.config.refresh_interval_seconds == 60

    class TestGetDashboard:
        async def test_get_dashboard(self, builder: DashboardBuilder) -> None:
            await builder.create_dashboard(dashboard_id="d1", name="Test")
            dashboard = await builder.get_dashboard("d1")
            assert dashboard.name == "Test"

        async def test_get_dashboard_not_found(self, builder: DashboardBuilder) -> None:
            with pytest.raises(DashboardNotFoundError):
                await builder.get_dashboard("nonexistent")

    class TestListDashboards:
        async def test_list_empty(self, builder: DashboardBuilder) -> None:
            dashboards = await builder.list_dashboards()
            assert dashboards == []

        async def test_list_multiple(self, builder: DashboardBuilder) -> None:
            await builder.create_dashboard(dashboard_id="d1", name="A")
            await builder.create_dashboard(dashboard_id="d2", name="B")
            dashboards = await builder.list_dashboards()
            assert len(dashboards) == 2

    class TestUpdateDashboard:
        async def test_update_name(self, builder: DashboardBuilder) -> None:
            await builder.create_dashboard(dashboard_id="d1", name="Old")
            updated = await builder.update_dashboard("d1", name="New")
            assert updated.name == "New"

        async def test_update_not_found(self, builder: DashboardBuilder) -> None:
            with pytest.raises(DashboardNotFoundError):
                await builder.update_dashboard("nonexistent", name="X")

    class TestDeleteDashboard:
        async def test_delete_dashboard(self, builder: DashboardBuilder) -> None:
            await builder.create_dashboard(dashboard_id="d1", name="Test")
            await builder.delete_dashboard("d1")
            with pytest.raises(DashboardNotFoundError):
                await builder.get_dashboard("d1")

        async def test_delete_not_found(self, builder: DashboardBuilder) -> None:
            with pytest.raises(DashboardNotFoundError):
                await builder.delete_dashboard("nonexistent")

    class TestWidgets:
        async def test_add_widget(
            self, builder: DashboardBuilder, sample_widget: WidgetDefinition
        ) -> None:
            await builder.create_dashboard(dashboard_id="d1", name="Test")
            updated = await builder.add_widget("d1", sample_widget)
            assert len(updated.widgets) == 1
            assert updated.widgets[0].id == "w1"

        async def test_remove_widget(
            self, builder: DashboardBuilder, sample_widget: WidgetDefinition
        ) -> None:
            await builder.create_dashboard(dashboard_id="d1", name="Test")
            await builder.add_widget("d1", sample_widget)
            updated = await builder.remove_widget("d1", "w1")
            assert len(updated.widgets) == 0

        async def test_remove_widget_not_found(self, builder: DashboardBuilder) -> None:
            await builder.create_dashboard(dashboard_id="d1", name="Test")
            with pytest.raises(DashboardNotFoundError):
                await builder.remove_widget("d1", "nonexistent")

    class TestRender:
        async def test_render(self, builder: DashboardBuilder) -> None:
            await builder.create_dashboard(dashboard_id="d1", name="Test")
            rendered = await builder.render("d1")
            assert rendered["name"] == "Test"
            assert "widgets" in rendered
            assert "config" in rendered

        async def test_render_not_found(self, builder: DashboardBuilder) -> None:
            with pytest.raises(DashboardNotFoundError):
                await builder.render("nonexistent")
