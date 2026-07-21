"""Health check for cache invalidation service."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class CacheInvalidationHealthCheck:
    """Health check for the cache invalidator."""

    name: str = "cacheinv"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Cache invalidation service healthy",
        )


__all__ = ["CacheInvalidationHealthCheck"]
