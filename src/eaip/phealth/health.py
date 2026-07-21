"""Health check for platform health subsystem."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class PlatformHealthHealthCheck:
    """Health check for the platform health subsystem."""

    name: str = "phealth"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Platform health subsystem healthy",
        )


__all__ = ["PlatformHealthHealthCheck"]
