"""KpiEngine — evaluates KPIs against targets with GoalTracker integration."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from eaip.analytics.exceptions import MetricNotFoundError
from eaip.analytics.models import AggregationType, MetricDefinition, MetricType, TrendDirection
from eaip.analytics.service import AnalyticsService
from eaip.analytics.trends import TrendAnalyzer
from eaip.goals.exceptions import KpiNotFoundError
from eaip.goals.models import KpiDefinition, KpiDirection
from eaip.goals.tracker import GoalTracker
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class KpiEngine:
    """Evaluates KPIs against targets and integrates with GoalTracker."""

    def __init__(
        self,
        analytics_service: AnalyticsService | None = None,
        goal_tracker: GoalTracker | None = None,
        trend_analyzer: TrendAnalyzer | None = None,
    ) -> None:
        self._analytics = analytics_service or AnalyticsService()
        self._tracker = goal_tracker or GoalTracker()
        self._trends = trend_analyzer or TrendAnalyzer(analytics_service=self._analytics)
        self._log = get_logger("eaip.analytics.kpi_engine")

    async def record_kpi_value(self, kpi_id: str, value: float, timestamp: datetime | None = None) -> float:
        """Record a KPI measurement and return the previous value."""
        return await self._tracker.record_kpi(kpi_id, value, timestamp)

    async def evaluate_kpi(self, kpi_id: str, current_value: float | None = None) -> dict[str, Any]:
        """Evaluate a KPI against its target and return status."""
        if kpi_id not in self._tracker._kpis:
            raise KpiNotFoundError(kpi_id)

        kpi = self._tracker._kpis[kpi_id]
        value = current_value if current_value is not None else kpi.current_value

        if kpi.target_value == 0:
            return {"kpi_id": kpi_id, "status": "met", "progress": 1.0, "current_value": value, "target_value": 0.0}

        if kpi.direction is KpiDirection.HIGHER_IS_BETTER:
            progress = min(value / kpi.target_value, 1.0)
            status = "met" if value >= kpi.target_value * kpi.met_threshold else "not_met"
        else:
            progress = min(kpi.target_value / max(value, 0.001), 1.0)
            status = "met" if value <= kpi.target_value * (2.0 - kpi.met_threshold) else "not_met"

        return {
            "kpi_id": kpi_id,
            "status": status,
            "progress": round(progress, 4),
            "current_value": value,
            "target_value": kpi.target_value,
        }

    async def get_kpi_status(self, kpi_id: str) -> dict[str, Any]:
        """Get the current met/not-met status for a KPI."""
        if kpi_id not in self._tracker._kpis:
            raise KpiNotFoundError(kpi_id)
        return await self._tracker.check_kpi_status(kpi_id)

    async def get_kpi_trend(self, kpi_id: str) -> str:
        """Get the trend direction for a KPI."""
        return await self._tracker.calculate_kpi_trend(kpi_id)

    async def list_kpis(self, goal_id: str | None = None) -> list[KpiDefinition]:
        """List all registered KPIs, optionally filtered by goal."""
        kpis = list(self._tracker._kpis.values())
        return kpis


__all__ = ["KpiEngine"]
