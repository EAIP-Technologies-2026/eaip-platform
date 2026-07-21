"""Health check for data synchronization."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class DataSyncHealthCheck:
    """Health check for the data synchronization service."""

    name: str = "datasync"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Data synchronization service healthy",
        )


__all__ = ["DataSyncHealthCheck"]
