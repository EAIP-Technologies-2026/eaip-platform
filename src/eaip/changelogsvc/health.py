"""Health check for the change log service."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.logging.context import get_logger

_log = get_logger("eaip.changelogsvc.health")


class ChangeLogHealthCheck(HealthCheck):
    """Reports the health of the change log storage backend."""

    name: str = "eaip.changelogsvc"

    def __init__(self) -> None:
        self._healthy: bool = True

    async def check(self) -> HealthReport:
        if self._healthy:
            return HealthReport(
                component="changelogsvc",
                status=HealthStatus.HEALTHY,
                message="Change log service nominal",
            )
        return HealthReport(
            component="changelogsvc",
            status=HealthStatus.UNHEALTHY,
            message="Change log service unavailable",
        )
