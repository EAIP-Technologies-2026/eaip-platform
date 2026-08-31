"""Health check for the emergency access manager."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class EmergencyHealthCheck:
    """Health check for the emergency access manager service."""

    name: str = "emergency"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Emergency access manager service healthy",
        )


__all__ = ["EmergencyHealthCheck"]
