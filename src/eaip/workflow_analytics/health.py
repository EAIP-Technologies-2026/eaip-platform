"""WorkflowAnalyticsHealthCheck — reports workflow analytics subsystem health."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.workflow_analytics.service import WorkflowAnalyticsService


class WorkflowAnalyticsHealthCheck(HealthCheck):
    """Reports workflow analytics subsystem health based on service state."""

    name: str = "eaip.workflow_analytics"

    def __init__(self, service: WorkflowAnalyticsService | None = None) -> None:
        self._service = service or WorkflowAnalyticsService()

    async def check(self) -> HealthReport:
        reports = await self._service.list_reports()
        details = {
            "reports_count": len(reports),
            "enabled": self._service.config.enabled,
            "retention_days": self._service.config.retention_days,
            "bottleneck_detection": self._service.config.enable_bottleneck_detection,
            "trend_analysis": self._service.config.enable_trend_analysis,
            "sla_tracking": self._service.config.enable_sla_tracking,
        }

        if not self._service.config.enabled:
            return HealthReport(
                component="WorkflowAnalyticsService",
                status=HealthStatus.DEGRADED,
                details=details,
                message="workflow analytics is disabled",
            )

        return HealthReport(
            component="WorkflowAnalyticsService",
            status=HealthStatus.HEALTHY,
            details=details,
        )


__all__ = ["WorkflowAnalyticsHealthCheck"]
