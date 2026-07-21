"""Health check for the compliance report generator."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.logging.context import get_logger

_log = get_logger("eaip.compliancegen.health")


class ComplianceHealthCheck(HealthCheck):
    """Reports the health of the compliance report generator."""

    name: str = "eaip.compliancegen"

    def __init__(self) -> None:
        self._healthy: bool = True

    async def check(self) -> HealthReport:
        if self._healthy:
            return HealthReport(
                component="compliancegen",
                status=HealthStatus.HEALTHY,
                message="Compliance report generator nominal",
            )
        return HealthReport(
            component="compliancegen",
            status=HealthStatus.UNHEALTHY,
            message="Compliance report generator unavailable",
        )
