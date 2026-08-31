"""WorkflowMonitorHealthCheck — reports workflow monitoring subsystem health."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.workflow_monitoring.service import WorkflowMonitorService


class WorkflowMonitorHealthCheck(HealthCheck):
    """Reports workflow monitoring subsystem health based on registered monitors and alerts."""

    name: str = "eaip.workflow_monitoring"

    def __init__(self, service: WorkflowMonitorService | None = None) -> None:
        """Initialize WorkflowMonitorHealthCheck.

        Args:
            service: An optional WorkflowMonitorService instance.
        """
        self._service = service or WorkflowMonitorService()

    async def check(self) -> HealthReport:
        """Run the health check and return a HealthReport.

        Returns:
            A HealthReport with status HEALTHY, DEGRADED, or UNHEALTHY.
        """
        configs = await self._service.list_configs()
        alerts = await self._service.list_alerts(unresolved_only=True)
        config_count = len(configs)
        unresolved_count = len(alerts)

        details = {
            "configs_total": config_count,
            "unresolved_alerts": unresolved_count,
        }

        if config_count == 0:
            return HealthReport(
                component="WorkflowMonitorService",
                status=HealthStatus.DEGRADED,
                details=details,
                message="no monitor configs registered",
            )

        if unresolved_count > 0:
            return HealthReport(
                component="WorkflowMonitorService",
                status=HealthStatus.DEGRADED,
                details=details,
                message=f"{unresolved_count} unresolved alert(s)",
            )

        return HealthReport(
            component="WorkflowMonitorService",
            status=HealthStatus.HEALTHY,
            details=details,
        )


__all__ = ["WorkflowMonitorHealthCheck"]
