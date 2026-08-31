"""DashboardBuilder — create, manage, and render custom dashboards."""

from __future__ import annotations

from eaip.dashboard.events import DashboardCreated, DashboardDeleted, DashboardUpdated, WidgetAdded
from eaip.dashboard.exceptions import DashboardNotFoundError
from eaip.dashboard.models import Dashboard, DashboardConfig, WidgetDefinition
from eaip.logging.context import get_logger


class DashboardBuilder:
    def __init__(self) -> None:
        self._dashboards: dict[str, Dashboard] = {}
        self._log = get_logger("eaip.dashboard.builder")

    async def create_dashboard(
        self,
        dashboard_id: str,
        name: str,
        description: str = "",
        config: DashboardConfig | None = None,
    ) -> Dashboard:
        dashboard = Dashboard(
            id=dashboard_id,
            name=name,
            description=description,
            config=config or DashboardConfig(),
        )
        self._dashboards[dashboard_id] = dashboard
        DashboardCreated(dashboard_id=dashboard_id, name=name)
        self._log.info("dashboard.created", dashboard_id=dashboard_id)
        return dashboard

    async def get_dashboard(self, dashboard_id: str) -> Dashboard:
        dashboard = self._dashboards.get(dashboard_id)
        if dashboard is None:
            raise DashboardNotFoundError(f"Dashboard '{dashboard_id}' not found")
        return dashboard

    async def list_dashboards(self) -> list[Dashboard]:
        return list(self._dashboards.values())

    async def update_dashboard(self, dashboard_id: str, **updates: str) -> Dashboard:
        dashboard = await self.get_dashboard(dashboard_id)
        updated = dashboard.model_copy(update=updates, deep=True)
        self._dashboards[dashboard_id] = updated
        DashboardUpdated(dashboard_id=dashboard_id, changes=updates)
        self._log.info("dashboard.updated", dashboard_id=dashboard_id)
        return updated

    async def delete_dashboard(self, dashboard_id: str) -> None:
        if dashboard_id not in self._dashboards:
            raise DashboardNotFoundError(f"Dashboard '{dashboard_id}' not found")
        del self._dashboards[dashboard_id]
        DashboardDeleted(dashboard_id=dashboard_id)
        self._log.info("dashboard.deleted", dashboard_id=dashboard_id)

    async def add_widget(self, dashboard_id: str, widget: WidgetDefinition) -> Dashboard:
        dashboard = await self.get_dashboard(dashboard_id)
        widgets = list(dashboard.widgets) + [widget]
        updated = dashboard.model_copy(update={"widgets": tuple(widgets)}, deep=True)
        self._dashboards[dashboard_id] = updated
        WidgetAdded(
            dashboard_id=dashboard_id,
            widget_id=widget.id,
            widget_type=widget.widget_type.value,
        )
        self._log.info("dashboard.widget.added", dashboard_id=dashboard_id, widget_id=widget.id)
        return updated

    async def remove_widget(self, dashboard_id: str, widget_id: str) -> Dashboard:
        dashboard = await self.get_dashboard(dashboard_id)
        widgets = [w for w in dashboard.widgets if w.id != widget_id]
        if len(widgets) == len(dashboard.widgets):
            raise DashboardNotFoundError(
                f"Widget '{widget_id}' not found in dashboard '{dashboard_id}'"
            )
        updated = dashboard.model_copy(update={"widgets": tuple(widgets)}, deep=True)
        self._dashboards[dashboard_id] = updated
        self._log.info("dashboard.widget.removed", dashboard_id=dashboard_id, widget_id=widget_id)
        return updated

    async def render(self, dashboard_id: str) -> dict[str, object]:
        dashboard = await self.get_dashboard(dashboard_id)
        return {
            "id": dashboard.id,
            "name": dashboard.name,
            "description": dashboard.description,
            "widgets": [w.model_dump() for w in dashboard.widgets],
            "config": dashboard.config.model_dump(),
        }


__all__ = ["DashboardBuilder"]
