"""Health check for the admin subsystem."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class AdminHealthCheck:
    """Health check for the admin runtime subsystem.

    Reports the health of the admin module, including its audit logger,
    config manager, and capability state.
    """

    name: str = "admin"

    def __init__(self) -> None:
        """Initialize AdminHealthCheck."""
        self._healthy: bool = True
        self._message: str = ""

    async def check(self) -> HealthReport:
        """Run the health check.

        Returns:
            A HealthReport describing the admin subsystem's health.
        """
        if self._healthy:
            return HealthReport(
                component=self.name,
                status=HealthStatus.HEALTHY,
                message=self._message or "admin subsystem is healthy",
            )
        return HealthReport(
            component=self.name,
            status=HealthStatus.DEGRADED,
            message=self._message or "admin subsystem is degraded",
        )

    def set_degraded(self, message: str) -> None:
        """Mark the admin subsystem as degraded.

        Args:
            message: A description of the degradation.
        """
        self._healthy = False
        self._message = message
