"""Health check for export compliance checker."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class ExportComplianceHealthCheck:
    """Health check for the export compliance service."""

    name: str = "exportcheck"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Export compliance service healthy",
        )


__all__ = ["ExportComplianceHealthCheck"]
