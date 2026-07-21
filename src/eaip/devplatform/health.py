"""Health check for the Developer API & SDK Platform."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class DevPlatformHealthCheck:
    """Health check for the developer platform subsystem.

    Reports the health of the API version manager, key manager, analytics
    service, and playground.
    """

    name: str = "devplatform"

    def __init__(self) -> None:
        """Initialize DevPlatformHealthCheck."""
        self._healthy: bool = True
        self._message: str = ""

    async def check(self) -> HealthReport:
        """Run the health check.

        Returns:
            A HealthReport describing the developer platform's health.
        """
        if self._healthy:
            return HealthReport(
                component=self.name,
                status=HealthStatus.HEALTHY,
                message=self._message or "developer platform is healthy",
            )
        return HealthReport(
            component=self.name,
            status=HealthStatus.DEGRADED,
            message=self._message or "developer platform is degraded",
        )

    def set_degraded(self, message: str) -> None:
        """Mark the developer platform as degraded.

        Args:
            message: A description of the degradation.
        """
        self._healthy = False
        self._message = message
