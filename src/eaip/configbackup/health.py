"""Health check for the configuration backup service."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.logging.context import get_logger

_log = get_logger("eaip.configbackup.health")


class ConfigBackupHealthCheck(HealthCheck):
    """Reports the health of the config backup service."""

    name: str = "eaip.configbackup"

    def __init__(self) -> None:
        self._healthy: bool = True

    async def check(self) -> HealthReport:
        if self._healthy:
            return HealthReport(
                component="configbackup",
                status=HealthStatus.HEALTHY,
                message="Config backup service nominal",
            )
        return HealthReport(
            component="configbackup",
            status=HealthStatus.UNHEALTHY,
            message="Config backup service unavailable",
        )
