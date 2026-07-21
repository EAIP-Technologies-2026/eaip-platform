"""Health check for the SDK subsystem."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class SdkHealthCheck:
    """Health check for the SDK subsystem.

    Reports the health of SDK definitions, client registrations,
    and build state.
    """

    name: str = "sdk"

    def __init__(self) -> None:
        """Initialize SdkHealthCheck."""
        self._healthy: bool = True
        self._message: str = ""

    async def check(self) -> HealthReport:
        """Run the health check.

        Returns:
            A HealthReport describing the SDK subsystem's health.
        """
        if self._healthy:
            return HealthReport(
                component=self.name,
                status=HealthStatus.HEALTHY,
                message=self._message or "SDK subsystem is healthy",
            )
        return HealthReport(
            component=self.name,
            status=HealthStatus.DEGRADED,
            message=self._message or "SDK subsystem is degraded",
        )

    def set_degraded(self, message: str) -> None:
        """Mark the SDK subsystem as degraded.

        Args:
            message: A description of the degradation.
        """
        self._healthy = False
        self._message = message
