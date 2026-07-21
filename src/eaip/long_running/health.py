"""Health check for long-running workflows."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus
from eaip.long_running.service import LongRunningService


class LongRunningHealthCheck:
    name: str = "long_running"

    def __init__(self, service: LongRunningService | None = None) -> None:
        self._service = service or LongRunningService()

    async def check(self) -> HealthReport:
        error_details: list[str] = []
        workflow_count = len(self._service.workflows)
        checkpoint_count = len(self._service.checkpoints)

        if workflow_count == 0:
            error_details.append("No long-running workflows registered")

        status = HealthStatus.HEALTHY
        if error_details:
            status = HealthStatus.DEGRADED

        return HealthReport(
            component="long_running",
            status=status,
            message="; ".join(error_details)
            if error_details
            else "Long-running workflow service is operational",
            details={
                "workflows_registered": workflow_count,
                "checkpoints_total": checkpoint_count,
            },
        )


__all__ = ["LongRunningHealthCheck"]
