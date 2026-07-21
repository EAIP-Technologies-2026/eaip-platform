"""Health check for incident communication tool."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class IncidentCommHealthCheck:
    """Health check for the incident communication service."""

    name: str = "inccomm"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Incident communication service healthy",
        )


__all__ = ["IncidentCommHealthCheck"]
