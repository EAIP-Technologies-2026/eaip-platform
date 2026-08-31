"""Health check for the execution history subsystem."""

from __future__ import annotations

from eaip.execution_history.service import ExecutionHistoryService
from eaip.health.checks import HealthReport, HealthStatus


class ExecutionHistoryHealthCheck:
    name: str = "execution_history"

    def __init__(self, service: ExecutionHistoryService) -> None:
        self._service = service

    async def check(self) -> HealthReport:
        error_details: list[str] = []
        total_records = len(self._service._records)

        if total_records == 0:
            error_details.append("No execution records stored")

        status = HealthStatus.HEALTHY
        if error_details:
            status = HealthStatus.DEGRADED

        return HealthReport(
            component="execution_history",
            status=status,
            message="; ".join(error_details)
            if error_details
            else "Execution history subsystem is operational",
            details={
                "total_records": total_records,
            },
        )


__all__ = ["ExecutionHistoryHealthCheck"]
