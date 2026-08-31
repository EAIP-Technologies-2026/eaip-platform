"""Health check for the operations subsystem."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus
from eaip.logging.context import get_logger
from eaip.operations.maintenance import MaintenanceManager


class OperationsHealthCheck:
    """Health check for the operations subsystem.

    Reports the health of maintenance, backup, migration, and
    health dashboard components.
    """

    name: str = "operations"

    def __init__(self, maintenance_manager: MaintenanceManager | None = None) -> None:
        """Initialize OperationsHealthCheck.

        Args:
            maintenance_manager: Optional MaintenanceManager instance.
        """
        self._maintenance_manager = maintenance_manager
        self._healthy: bool = True
        self._message: str = ""
        self._log = get_logger("eaip.operations.health")

    async def check(self) -> HealthReport:
        """Run the health check.

        Returns:
            A HealthReport describing the operations subsystem's health.
        """
        children: list[HealthReport] = []

        if self._maintenance_manager is not None:
            active_count = len(self._maintenance_manager.active_components)
            if active_count > 0:
                children.append(
                    HealthReport(
                        component="operations.maintenance",
                        status=HealthStatus.DEGRADED,
                        message=f"{active_count} component(s) in maintenance mode",
                    )
                )
            else:
                children.append(
                    HealthReport(
                        component="operations.maintenance",
                        status=HealthStatus.HEALTHY,
                        message="No active maintenance windows",
                    )
                )

        if self._healthy and not any(
            c.status is HealthStatus.DEGRADED or c.status is HealthStatus.UNHEALTHY
            for c in children
        ):
            return HealthReport(
                component=self.name,
                status=HealthStatus.HEALTHY,
                message=self._message or "operations subsystem is healthy",
                children=tuple(children),
            )
        return HealthReport(
            component=self.name,
            status=HealthStatus.DEGRADED,
            message=self._message or "operations subsystem is degraded",
            children=tuple(children),
        )

    def set_degraded(self, message: str) -> None:
        """Mark the operations subsystem as degraded.

        Args:
            message: A description of the degradation.
        """
        self._healthy = False
        self._message = message


__all__ = ["OperationsHealthCheck"]
