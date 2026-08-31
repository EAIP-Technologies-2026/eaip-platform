"""Health check for the retry orchestration."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.retry_orchestration.models import RetryStateStatus
from eaip.retry_orchestration.service import RetryOrchestrationService


class RetryOrchestrationHealthCheck(HealthCheck):
    """Reports retry orchestration health based on policy and execution counts."""

    name: str = "eaip.retry_orchestration"

    def __init__(self, service: RetryOrchestrationService | None = None) -> None:
        self._service = service or RetryOrchestrationService()

    async def check(self) -> HealthReport:
        policies = await self._service.list_policies()
        executions = await self._service.list_executions()

        failed_count = sum(1 for e in executions if e.status == RetryStateStatus.FAILED)
        exhausted_count = sum(1 for e in executions if e.status == RetryStateStatus.EXHAUSTED)
        running_count = sum(1 for e in executions if e.status == RetryStateStatus.RUNNING)

        details = {
            "policies_defined": len(policies),
            "executions_total": len(executions),
            "executions_running": running_count,
            "executions_failed": failed_count,
            "executions_exhausted": exhausted_count,
        }

        if failed_count > 0:
            return HealthReport(
                component="RetryOrchestration",
                status=HealthStatus.DEGRADED,
                details=details,
                message=f"{failed_count} failed retry execution(s) detected",
            )
        if exhausted_count > 0:
            return HealthReport(
                component="RetryOrchestration",
                status=HealthStatus.DEGRADED,
                details=details,
                message=f"{exhausted_count} exhausted retry execution(s) detected",
            )
        return HealthReport(
            component="RetryOrchestration",
            status=HealthStatus.HEALTHY,
            details=details,
        )


__all__ = ["RetryOrchestrationHealthCheck"]
