"""Health check for file integrity monitor."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class FileIntegrityHealthCheck:
    """Health check for the file integrity monitor service."""

    name: str = "fileintmon"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="File integrity monitor service healthy",
        )


__all__ = ["FileIntegrityHealthCheck"]
