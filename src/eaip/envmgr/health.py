"""Health check for environment variable management."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class EnvMgrHealthCheck:
    """Health check for the environment variable manager service."""

    name: str = "envmgr"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Environment variable manager service healthy",
        )


__all__ = ["EnvMgrHealthCheck"]
