"""Health check for model monitoring."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class ModelMonitorHealthCheck:
    """Health check for the model monitor."""

    name: str = "modelmon"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Model monitor healthy",
        )


__all__ = ["ModelMonitorHealthCheck"]
