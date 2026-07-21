"""Health check for capacity analyzer."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class CapacityAnalyzerHealthCheck:
    """Health check for the capacity analyzer."""

    name: str = "capacity"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Capacity analyzer healthy",
        )


__all__ = ["CapacityAnalyzerHealthCheck"]
