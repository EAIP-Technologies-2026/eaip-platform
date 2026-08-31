"""Health check for the cache subsystem."""

from __future__ import annotations

from eaip.cache.manager import CacheManager
from eaip.cache.provider import CacheProvider
from eaip.health.checks import HealthCheck, HealthReport, HealthStatus

_LOW_HIT_RATIO_THRESHOLD = 0.1
_MIN_TOTAL_REQUESTS_FOR_DEGRADED = 100


class CacheHealthCheck(HealthCheck):
    """Reports cache health based on provider stats and hit ratios."""

    name: str = "eaip.cache"

    def __init__(
        self,
        provider: CacheProvider | None = None,
        manager: CacheManager | None = None,
    ) -> None:
        """Initialize with either a provider or manager."""
        self._provider = provider
        self._manager = manager

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        try:
            if self._manager is not None:
                stats = await self._manager.get_stats()
            elif self._provider is not None:
                stats = await self._provider.get_stats()
            else:
                return HealthReport(
                    component="cache",
                    status=HealthStatus.UNHEALTHY,
                    message="No cache provider or manager configured",
                )

            details: dict[str, object] = {
                "total_entries": stats.total_entries,
                "total_hits": stats.total_hits,
                "total_misses": stats.total_misses,
                "total_evictions": stats.total_evictions,
                "hit_ratio": stats.hit_ratio,
                "size_bytes": stats.size_bytes,
            }

            total_requests = stats.total_hits + stats.total_misses
            degraded = (
                stats.hit_ratio < _LOW_HIT_RATIO_THRESHOLD
                and total_requests > _MIN_TOTAL_REQUESTS_FOR_DEGRADED
            )
            if degraded:
                return HealthReport(
                    component="cache",
                    status=HealthStatus.DEGRADED,
                    message=f"Low cache hit ratio: {stats.hit_ratio:.2%}",
                    details=details,
                )

            return HealthReport(
                component="cache",
                status=HealthStatus.HEALTHY,
                message="Cache subsystem nominal",
                details=details,
            )

        except Exception as exc:
            return HealthReport(
                component="cache",
                status=HealthStatus.UNHEALTHY,
                message=f"Cache health check failed: {exc}",
            )
