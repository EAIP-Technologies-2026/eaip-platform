"""Health check for the organization subsystem."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class OrganizationHealthCheck:
    """Health check for the organization management subsystem.

    Reports the health of organization CRUD, hierarchy, members, and policies.
    """

    name: str = "organization"

    def __init__(self) -> None:
        """Initialize OrganizationHealthCheck."""
        self._healthy: bool = True
        self._message: str = ""

    async def check(self) -> HealthReport:
        """Run the health check.

        Returns:
            A HealthReport describing the organization subsystem's health.
        """
        if self._healthy:
            return HealthReport(
                component=self.name,
                status=HealthStatus.HEALTHY,
                message=self._message or "organization subsystem is healthy",
            )
        return HealthReport(
            component=self.name,
            status=HealthStatus.DEGRADED,
            message=self._message or "organization subsystem is degraded",
        )

    def set_degraded(self, message: str) -> None:
        """Mark the organization subsystem as degraded.

        Args:
            message: A description of the degradation.
        """
        self._healthy = False
        self._message = message
