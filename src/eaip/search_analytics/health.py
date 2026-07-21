"""Search analytics health check — implements the HealthCheck protocol."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus
from eaip.logging.context import get_logger


class SearchAnalyticsHealthCheck:
    """Health check for the search analytics system."""

    name: str = "search_analytics"

    def __init__(self, query_log_count: int = 0) -> None:
        self._query_log_count = query_log_count
        self._log = get_logger("eaip.search_analytics.health")

    @property
    def query_log_count(self) -> int:
        return self._query_log_count

    async def check(self) -> HealthReport:
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message=f"{self._query_log_count} query log(s) recorded.",
            details={"query_log_count": self._query_log_count},
        )


__all__ = ["SearchAnalyticsHealthCheck"]
