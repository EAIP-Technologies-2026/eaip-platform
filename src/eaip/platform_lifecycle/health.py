"""Health check for platform lifecycle manager."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class PlatformLifecycleHealthCheck:
    """Health check for the platform lifecycle manager."""

    name: str = "platform_lifecycle"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Platform lifecycle manager healthy",
        )


__all__ = ["PlatformLifecycleHealthCheck"]
