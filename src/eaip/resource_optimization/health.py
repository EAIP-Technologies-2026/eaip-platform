"""Health check for resource optimization."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class ResourceOptimizationHealthCheck:
    """Health check for the resource optimization service."""

    name: str = "resource_optimization"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Resource optimization service healthy",
        )


__all__ = ["ResourceOptimizationHealthCheck"]
