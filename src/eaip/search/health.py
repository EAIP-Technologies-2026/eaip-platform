"""Search health check — implements the HealthCheck protocol."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.logging.context import get_logger


class SearchHealthCheck:
    """Health check for the search system.

    Reports healthy when the search engine has at least one registered
    provider; degraded otherwise.
    """

    name: str = "search"

    def __init__(self, provider_count: int = 0) -> None:
        self._provider_count = provider_count
        self._log = get_logger("eaip.search.health")

    @property
    def provider_count(self) -> int:
        return self._provider_count

    async def check(self) -> HealthReport:
        """Run the search health check.

        Returns:
            A HealthReport describing the health of the search system.
        """
        if self._provider_count > 0:
            return HealthReport(
                component=self.name,
                status=HealthStatus.HEALTHY,
                message=f"{self._provider_count} provider(s) registered.",
                details={"provider_count": self._provider_count},
            )

        return HealthReport(
            component=self.name,
            status=HealthStatus.DEGRADED,
            message="No search providers registered.",
            details={"provider_count": 0},
        )


__all__ = ["SearchHealthCheck"]
