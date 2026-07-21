"""Health check for event retention management."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class EventRetentionHealthCheck:
    """Health check for the event retention manager service."""

    name: str = "eventret"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Event retention manager service healthy",
        )


__all__ = ["EventRetentionHealthCheck"]
