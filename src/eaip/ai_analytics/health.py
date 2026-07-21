"""AiAnalyticsHealthCheck — reports AI analytics subsystem health."""

from __future__ import annotations

from eaip.ai_analytics.service import AiAnalyticsService
from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class AiAnalyticsHealthCheck(HealthCheck):
    """Reports AI analytics subsystem health based on registered metrics and service state."""

    name: str = "eaip.ai_analytics"

    def __init__(self, service: AiAnalyticsService | None = None) -> None:
        self._service = service or AiAnalyticsService()

    async def check(self) -> HealthReport:
        metrics = await self._service.list_metrics()
        metric_count = len(metrics)

        details = {
            "metrics_total": metric_count,
            "enabled": self._service.config.enabled,
            "anomaly_detection": self._service.config.anomaly_detection_enabled,
            "trend_detection": self._service.config.trend_detection_enabled,
            "forecast_enabled": self._service.config.forecast_enabled,
            "export_enabled": self._service.config.export_enabled,
            "retention_days": self._service.config.retention_days,
        }

        if not self._service.config.enabled:
            return HealthReport(
                component="AiAnalyticsService",
                status=HealthStatus.DEGRADED,
                details=details,
                message="AI analytics is disabled",
            )

        return HealthReport(
            component="AiAnalyticsService",
            status=HealthStatus.HEALTHY,
            details=details,
        )


__all__ = ["AiAnalyticsHealthCheck"]
