"""AnalyticsHealthCheck — reports analytics subsystem health."""

from __future__ import annotations

from eaip.analytics.service import AnalyticsService
from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class AnalyticsHealthCheck(HealthCheck):
    """Reports analytics subsystem health based on registered metrics and service state."""

    name: str = "eaip.analytics"

    def __init__(self, analytics_service: AnalyticsService | None = None) -> None:
        self._service = analytics_service or AnalyticsService()

    async def check(self) -> HealthReport:
        metrics = await self._service.list_metrics()
        metric_count = len(metrics)
        enabled_count = sum(1 for m in metrics if m.enabled)

        details = {
            "metrics_total": metric_count,
            "metrics_enabled": enabled_count,
            "retention_days": self._service.config.retention_days,
            "trend_detection": self._service.config.enable_trend_detection,
            "anomaly_detection": self._service.config.enable_anomaly_detection,
        }

        if metric_count == 0:
            return HealthReport(
                component="AnalyticsService",
                status=HealthStatus.DEGRADED,
                details=details,
                message="no metrics registered",
            )

        return HealthReport(
            component="AnalyticsService",
            status=HealthStatus.HEALTHY,
            details=details,
        )


__all__ = ["AnalyticsHealthCheck"]
