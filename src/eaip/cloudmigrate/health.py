"""Health check for the cloud migration assistant."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.logging.context import get_logger

_log = get_logger("eaip.cloudmigrate.health")


class MigrationHealthCheck(HealthCheck):
    """Reports the health of the migration assistant."""

    name: str = "eaip.cloudmigrate"

    def __init__(self) -> None:
        self._healthy: bool = True

    async def check(self) -> HealthReport:
        if self._healthy:
            return HealthReport(
                component="cloudmigrate",
                status=HealthStatus.HEALTHY,
                message="Cloud migration assistant nominal",
            )
        return HealthReport(
            component="cloudmigrate",
            status=HealthStatus.UNHEALTHY,
            message="Cloud migration assistant unavailable",
        )
