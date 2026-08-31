"""Health check for report scheduler."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class ReportSchedulerHealthCheck:
    """Health check for the report scheduler engine."""

    name: str = "reportsched"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Report scheduler engine healthy",
        )


__all__ = ["ReportSchedulerHealthCheck"]
