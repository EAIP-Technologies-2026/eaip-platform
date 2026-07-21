"""Health check for rate limiting."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class ThrottleHealthCheck:
    """Health check for rate limiting."""

    name: str = "throttle"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Throttle engine healthy",
        )


__all__ = ["ThrottleHealthCheck"]
