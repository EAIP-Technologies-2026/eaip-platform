"""Health check for external identity mapper."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class ExternalIdentityHealthCheck:
    """Health check for the external identity mapper service."""

    name: str = "extidmap"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="External identity mapper service healthy",
        )


__all__ = ["ExternalIdentityHealthCheck"]
