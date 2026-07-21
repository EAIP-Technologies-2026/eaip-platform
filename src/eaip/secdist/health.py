"""Health check for the secrets distribution service."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class SecdistHealthCheck:
    """Health check for the secrets distribution service."""

    name: str = "secdist"

    def __init__(self, target_count: int = 0, distribution_count: int = 0) -> None:
        self._target_count = target_count
        self._distribution_count = distribution_count

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        details = {
            "target_count": self._target_count,
            "distribution_count": self._distribution_count,
        }
        if self._target_count > 0:
            return HealthReport(
                component=self.name,
                status=HealthStatus.HEALTHY,
                message=f"{self._target_count} target(s) registered, {self._distribution_count} distribution(s)",
                details=details,
            )
        return HealthReport(
            component=self.name,
            status=HealthStatus.DEGRADED,
            message="No distribution targets configured",
            details=details,
        )


__all__ = ["SecdistHealthCheck"]
