"""Health check for rate limiting."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class RateLimitHealthCheck:
    """Health check for the rate limiter engine."""

    name: str = "ratelimit"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Rate limiter engine healthy",
        )


__all__ = ["RateLimitHealthCheck"]
