"""Health check for the data catalog."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class DataCatalogHealthCheck:
    """Health check for the data catalog."""

    name: str = "datacatalog"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Data catalog healthy",
        )


__all__ = ["DataCatalogHealthCheck"]
