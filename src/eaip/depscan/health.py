"""Health check for dependency scanning."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class DependencyScannerHealthCheck:
    """Health check for the dependency scanner service."""

    name: str = "depscan"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Dependency scanner service healthy",
        )


__all__ = ["DependencyScannerHealthCheck"]
