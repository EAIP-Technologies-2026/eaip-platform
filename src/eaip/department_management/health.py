"""Health check for the department management subsystem."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class DepartmentManagementHealthCheck:
    """Health check for the department management subsystem.

    Reports the health of the department management module, including
    its service layer and data integrity.
    """

    name: str = "department_management"

    def __init__(self) -> None:
        """Initialize DepartmentManagementHealthCheck."""
        self._healthy: bool = True
        self._message: str = ""

    async def check(self) -> HealthReport:
        """Run the health check.

        Returns:
            A HealthReport describing the subsystem's health.
        """
        if self._healthy:
            return HealthReport(
                component=self.name,
                status=HealthStatus.HEALTHY,
                message=self._message or "department management subsystem is healthy",
            )
        return HealthReport(
            component=self.name,
            status=HealthStatus.DEGRADED,
            message=self._message or "department management subsystem is degraded",
        )

    def set_degraded(self, message: str) -> None:
        """Mark the subsystem as degraded.

        Args:
            message: A description of the degradation.
        """
        self._healthy = False
        self._message = message
