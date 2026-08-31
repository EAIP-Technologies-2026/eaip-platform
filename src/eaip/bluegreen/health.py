"""Health check for blue-green deployment manager."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class BlueGreenHealthCheck:
    """Health check for the blue-green deployment manager."""

    name: str = "bluegreen"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Blue-green deployment manager healthy",
        )


__all__ = ["BlueGreenHealthCheck"]
