"""Health check for the admin_api subsystem."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class AdminApiHealthCheck:
    """Health check for the admin API runtime subsystem.

    Reports the health of the admin API module, including its
    API definitions, versions, endpoints, and client management.
    """

    name: str = "admin_api"

    def __init__(self) -> None:
        """Initialize AdminApiHealthCheck."""
        self._healthy: bool = True
        self._message: str = ""

    async def check(self) -> HealthReport:
        """Run the health check.

        Returns:
            A HealthReport describing the admin API subsystem's health.
        """
        if self._healthy:
            return HealthReport(
                component=self.name,
                status=HealthStatus.HEALTHY,
                message=self._message or "admin API subsystem is healthy",
            )
        return HealthReport(
            component=self.name,
            status=HealthStatus.DEGRADED,
            message=self._message or "admin API subsystem is degraded",
        )

    def set_degraded(self, message: str) -> None:
        """Mark the admin API subsystem as degraded.

        Args:
            message: A description of the degradation.
        """
        self._healthy = False
        self._message = message


__all__ = ["AdminApiHealthCheck"]
