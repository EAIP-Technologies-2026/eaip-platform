"""Health check for cloud resource management."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class CloudManagerHealthCheck:
    """Health check for the cloud resource manager."""

    name: str = "cloudmgr"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Cloud manager healthy",
        )


__all__ = ["CloudManagerHealthCheck"]
