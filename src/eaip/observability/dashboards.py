from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from eaip.logging.context import get_logger
from eaip.observability.events import DashboardCreated, DashboardDeleted, DashboardUpdated
from eaip.observability.exceptions import DashboardNotFoundError
from eaip.observability.models import (
    DashboardWidget,
    DataPoint,
    ObservabilityConfig,
    ObservabilityDashboard,
)
from eaip.shared.time import utc_now


class DashboardService:
    name: str = "observability.dashboards"

    def __init__(
        self,
        config: ObservabilityConfig | None = None,
    ) -> None:
        self._config = config or ObservabilityConfig()
        self._dashboards: dict[str, ObservabilityDashboard] = {}
        self._log = get_logger("eaip.observability.dashboards")

    def create_dashboard(
        self,
        dashboard: ObservabilityDashboard,
    ) -> ObservabilityDashboard:
        self._dashboards[dashboard.id] = dashboard
        self._log.info("dashboard.created", id=dashboard.id, name=dashboard.name)
        DashboardCreated(dashboard_id=dashboard.id, dashboard_name=dashboard.name)
        return dashboard

    def get_dashboard(self, dashboard_id: str) -> ObservabilityDashboard:
        dash = self._dashboards.get(dashboard_id)
        if dash is None:
            raise DashboardNotFoundError(f"Dashboard {dashboard_id!r} not found")
        return dash

    def update_dashboard(
        self,
        dashboard_id: str,
        **updates: Any,
    ) -> ObservabilityDashboard:
        dash = self.get_dashboard(dashboard_id)
        updated = dash.model_copy(update={**updates, "updated_at": utc_now()})
        self._dashboards[dashboard_id] = updated
        self._log.info("dashboard.updated", id=dashboard_id)
        DashboardUpdated(dashboard_id=dashboard_id, dashboard_name=updated.name)
        return updated

    def delete_dashboard(self, dashboard_id: str) -> None:
        dash = self.get_dashboard(dashboard_id)
        del self._dashboards[dashboard_id]
        self._log.info("dashboard.deleted", id=dashboard_id)
        DashboardDeleted(dashboard_id=dashboard_id, dashboard_name=dash.name)

    def list_dashboards(
        self,
        enabled_only: bool = False,
    ) -> list[ObservabilityDashboard]:
        result = list(self._dashboards.values())
        if enabled_only:
            result = [d for d in result if d.enabled]
        return result

    async def render_dashboard(
        self,
        dashboard_id: str,
    ) -> dict[str, Any]:
        dash = self.get_dashboard(dashboard_id)
        timerange = timedelta(seconds=dash.refresh_interval_seconds)
        rendered_widgets = [await self.render_widget(w, timerange) for w in dash.widgets]
        return {
            "id": dash.id,
            "name": dash.name,
            "description": dash.description,
            "widgets": rendered_widgets,
            "refresh_interval_seconds": dash.refresh_interval_seconds,
            "metadata": dict(dash.metadata),
        }

    async def render_widget(
        self,
        widget: DashboardWidget,
        timerange: timedelta,
    ) -> dict[str, Any]:
        series: list[dict[str, Any]] = []
        for source in widget.metric_sources:
            points = await self.resolve_metric(source, timerange)
            series.append(
                {
                    "metric_source": source,
                    "data": [
                        {
                            "timestamp": p.timestamp.isoformat(),
                            "value": p.value,
                            "labels": dict(p.labels),
                        }
                        for p in points
                    ],
                }
            )
        return {
            "id": widget.id,
            "type": widget.type,
            "title": widget.title,
            "series": series,
            "config": dict(widget.config),
            "position": dict(widget.position),
            "width": widget.width,
            "height": widget.height,
        }

    async def resolve_metric(
        self,
        metric_source: str,
        timerange: timedelta,
    ) -> list[DataPoint]:
        now = utc_now()
        start = now - timerange
        return [
            DataPoint(
                timestamp=ts,
                value=0.0,
                labels={"source": metric_source},
            )
            for ts in self._generate_timestamps(start, now, 60)
        ]

    def _generate_timestamps(
        self,
        start: datetime,
        end: datetime,
        interval_seconds: int,
    ) -> list[datetime]:
        timestamps: list[datetime] = []
        current = start
        while current <= end:
            timestamps.append(current)
            current += timedelta(seconds=interval_seconds)
        return timestamps

    @property
    def config(self) -> ObservabilityConfig:
        return self._config

    @config.setter
    def config(self, value: ObservabilityConfig) -> None:
        self._config = value


__all__ = ["DashboardService"]
