"""Workflow health check - reports counts for active runs and engine state."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class WorkflowHealthCheck(HealthCheck):
    """Reports workflow engine health based on run-state counts."""

    name: str = "eaip.workflow.engine"

    def __init__(
        self,
        run_count: int = 0,
        running_count: int = 0,
        paused_count: int = 0,
        failed_count: int = 0,
        timed_out_count: int = 0,
        pending_approval_count: int = 0,
    ) -> None:
        self._run_count = run_count
        self._running_count = running_count
        self._paused_count = paused_count
        self._failed_count = failed_count
        self._timed_out_count = timed_out_count
        self._pending_approval_count = pending_approval_count

    async def check(self) -> HealthReport:
        details = {
            "total_runs": self._run_count,
            "running": self._running_count,
            "paused": self._paused_count,
            "failed": self._failed_count,
            "timed_out": self._timed_out_count,
            "pending_approval": self._pending_approval_count,
        }
        if self._failed_count > 0:
            return HealthReport(
                component="WorkflowEngine",
                status=HealthStatus.DEGRADED,
                details=details,
                message=f"{self._failed_count} failed workflow(s) detected",
            )
        if self._pending_approval_count > 0:
            return HealthReport(
                component="WorkflowEngine",
                status=HealthStatus.DEGRADED,
                details=details,
                message=f"{self._pending_approval_count} workflow(s) pending approval",
            )
        return HealthReport(
            component="WorkflowEngine",
            status=HealthStatus.HEALTHY,
            details=details,
        )


__all__ = [
    "WorkflowHealthCheck",
]
