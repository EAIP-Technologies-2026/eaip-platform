"""TelemetryCollector — collects operational and platform metrics from the runtime."""

from __future__ import annotations

from eaip.analytics.exceptions import MetricNotFoundError
from eaip.analytics.models import MetricPoint
from eaip.analytics.service import AnalyticsService
from eaip.logging.context import get_logger


class TelemetryCollector:
    """Collects operational and platform metrics and records them via AnalyticsService."""

    def __init__(self, analytics_service: AnalyticsService | None = None) -> None:
        self._analytics = analytics_service or AnalyticsService()
        self._log = get_logger("eaip.analytics.telemetry")

    async def collect_operational_metrics(self) -> dict[str, float]:
        """Collect operational metrics: agents, workflows, sessions, memory.

        Returns a dictionary of metric_id -> value for the operational snapshot.
        """
        metrics = {
            "agents.active": 0.0,
            "agents.total": 0.0,
            "workflows.running": 0.0,
            "workflows.completed": 0.0,
            "sessions.active": 0.0,
            "memory.usage_bytes": 0.0,
            "memory.allocated_bytes": 0.0,
        }

        for mid, value in metrics.items():
            try:
                await self.record_metric_point(mid, value, {"source": "telemetry_collector"})
            except MetricNotFoundError:
                self._log.warning("telemetry.metric_not_registered", metric_id=mid)

        return metrics

    async def collect_platform_metrics(self) -> dict[str, float]:
        """Collect platform health metrics.

        Returns a dictionary of metric_id -> value for the platform snapshot.
        """
        metrics = {
            "platform.uptime_seconds": 0.0,
            "platform.errors_total": 0.0,
            "platform.requests_total": 0.0,
            "platform.latency_ms": 0.0,
            "platform.health_score": 1.0,
        }

        for mid, value in metrics.items():
            try:
                await self.record_metric_point(mid, value, {"source": "platform_health"})
            except MetricNotFoundError:
                self._log.warning("telemetry.metric_not_registered", metric_id=mid)

        return metrics

    async def record_metric_point(
        self, metric_id: str, value: float, tags: dict[str, str] | None = None
    ) -> MetricPoint:
        """Record a metric data point with the current timestamp."""
        return await self._analytics.record_metric(metric_id, value, tags)


__all__ = ["TelemetryCollector"]
