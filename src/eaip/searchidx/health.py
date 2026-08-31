"""Search index health check — implements the HealthCheck protocol."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class SearchIndexHealthCheck:
    """Health check for the search index subsystem."""

    name: str = "searchidx"

    def __init__(
        self,
        index_count: int = 0,
        ready_indices: int = 0,
        cache_available: bool = True,
    ) -> None:
        """Initialize with index and cache status."""
        self._index_count = index_count
        self._ready_indices = ready_indices
        self._cache_available = cache_available

    @property
    def index_count(self) -> int:
        """Return the total number of indices."""
        return self._index_count

    @property
    def ready_indices(self) -> int:
        """Return the number of ready indices."""
        return self._ready_indices

    @property
    def cache_available(self) -> bool:
        """Return whether the cache is available."""
        return self._cache_available

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        details = {
            "index_count": self._index_count,
            "ready_indices": self._ready_indices,
            "cache_available": self._cache_available,
        }
        if self._cache_available and self._index_count > 0:
            return HealthReport(
                component=self.name,
                status=HealthStatus.HEALTHY,
                message=f"{self._ready_indices}/{self._index_count} index(es) ready.",
                details=details,
            )
        if self._index_count == 0:
            return HealthReport(
                component=self.name,
                status=HealthStatus.DEGRADED,
                message="No indices configured.",
                details=details,
            )
        return HealthReport(
            component=self.name,
            status=HealthStatus.DEGRADED,
            message="Cache unavailable or indices not ready.",
            details=details,
        )


__all__ = ["SearchIndexHealthCheck"]
