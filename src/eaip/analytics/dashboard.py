"""DashboardService — create, read, update, delete dashboards and render widgets."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from eaip.analytics.exceptions import DashboardNotFoundError
from eaip.analytics.models import (
    AggregationType,
    DashboardDefinition,
    DashboardWidget,
    TimeSeriesPoint,
    TimeSeriesResult,
)
from eaip.analytics.service import AnalyticsService
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class DashboardService:
    """Manages dashboard definitions and renders widget data."""

    def __init__(self, analytics_service: AnalyticsService | None = None) -> None:
        self._analytics = analytics_service or AnalyticsService()
        self._dashboards: dict[str, DashboardDefinition] = {}
        self._log = get_logger("eaip.analytics.dashboard")
        self._version_counter: int = 0

    async def create_dashboard(self, definition: DashboardDefinition) -> DashboardDefinition:
        """Create a new dashboard."""
        self._dashboards[definition.id] = definition
        self._log.info("analytics.dashboard.created", dashboard_id=definition.id, name=definition.name)
        return definition

    async def get_dashboard(self, dashboard_id: str) -> DashboardDefinition:
        """Get a dashboard by ID."""
        dashboard = self._dashboards.get(dashboard_id)
        if dashboard is None:
            raise DashboardNotFoundError(dashboard_id)
        return dashboard

    async def update_dashboard(self, dashboard_id: str, updates: dict[str, Any]) -> DashboardDefinition:
        """Update an existing dashboard."""
        existing = await self.get_dashboard(dashboard_id)

        name = updates.get("name", existing.name)
        description = updates.get("description", existing.description)
        widgets = updates.get("widgets", existing.widgets)
        refresh = updates.get("refresh_interval_seconds", existing.refresh_interval_seconds)
        metadata = updates.get("metadata", existing.metadata)

        updated = DashboardDefinition(
            id=dashboard_id,
            name=name,
            description=description,
            widgets=widgets,
            refresh_interval_seconds=refresh,
            metadata=metadata,
        )
        self._dashboards[dashboard_id] = updated
        self._version_counter += 1
        self._log.info("analytics.dashboard.updated", dashboard_id=dashboard_id)
        return updated

    async def delete_dashboard(self, dashboard_id: str) -> None:
        """Delete a dashboard by ID."""
        if dashboard_id not in self._dashboards:
            raise DashboardNotFoundError(dashboard_id)
        del self._dashboards[dashboard_id]
        self._log.info("analytics.dashboard.deleted", dashboard_id=dashboard_id)

    async def list_dashboards(self) -> list[DashboardDefinition]:
        """List all dashboards."""
        return list(self._dashboards.values())

    async def render_widget(
        self, widget_id: str, time_range: tuple[datetime, datetime]
    ) -> dict[str, Any]:
        """Render data for a specific widget across all dashboards."""
        for dashboard in self._dashboards.values():
            for widget in dashboard.widgets:
                if widget.id == widget_id:
                    return await self._render_widget_data(widget, time_range)

        raise DashboardNotFoundError(widget_id)

    async def render_dashboard(
        self, dashboard_id: str, time_range: tuple[datetime, datetime]
    ) -> dict[str, Any]:
        """Render all widgets for a full dashboard."""
        dashboard = await self.get_dashboard(dashboard_id)
        rendered_widgets: list[dict[str, Any]] = []

        for widget in dashboard.widgets:
            data = await self._render_widget_data(widget, time_range)
            rendered_widgets.append(data)

        return {
            "dashboard_id": dashboard_id,
            "name": dashboard.name,
            "widgets": rendered_widgets,
            "rendered_at": utc_now(),
        }

    async def _render_widget_data(
        self, widget: DashboardWidget, time_range: tuple[datetime, datetime]
    ) -> dict[str, Any]:
        """Render data for a single widget."""
        series_data: dict[str, TimeSeriesResult] = {}
        for mid in widget.metric_ids:
            try:
                result = await self._analytics.query_time_series(
                    mid, time_range[0], time_range[1], aggregation=AggregationType.AVG
                )
                series_data[mid] = result
            except Exception:
                series_data[mid] = TimeSeriesResult(
                    metric_id=mid,
                    points=(),
                    aggregation=AggregationType.AVG,
                    start_time=time_range[0],
                    end_time=time_range[1],
                )

        return {
            "widget_id": widget.id,
            "type": widget.type.value,
            "title": widget.title,
            "series": {
                mid: {"points": list(result.points), "aggregation": result.aggregation.value}
                for mid, result in series_data.items()
            },
        }


__all__ = ["DashboardService"]
