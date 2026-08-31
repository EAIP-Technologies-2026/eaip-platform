"""Workforce health check — reports registry and orchestrator health."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class WorkforceHealthCheck(HealthCheck):
    """Reports workforce subsystem health based on registry and assignment state."""

    name: str = "eaip.workforce"

    def __init__(
        self,
        worker_count: int = 0,
        available_count: int = 0,
        active_assignments: int = 0,
        failed_assignments: int = 0,
        scheduled_count: int = 0,
    ) -> None:
        self._worker_count = worker_count
        self._available_count = available_count
        self._active_assignments = active_assignments
        self._failed_assignments = failed_assignments
        self._scheduled_count = scheduled_count

    async def check(self) -> HealthReport:
        details = {
            "workers_registered": self._worker_count,
            "workers_available": self._available_count,
            "active_assignments": self._active_assignments,
            "failed_assignments": self._failed_assignments,
            "scheduled_workers": self._scheduled_count,
        }
        if self._failed_assignments > 0:
            return HealthReport(
                component="WorkforceRuntime",
                status=HealthStatus.DEGRADED,
                details=details,
                message=f"{self._failed_assignments} failed assignment(s) detected",
            )
        if self._active_assignments > 0 and self._worker_count == 0:
            return HealthReport(
                component="WorkforceRuntime",
                status=HealthStatus.DEGRADED,
                details=details,
                message="active assignments with no registered workers",
            )
        return HealthReport(
            component="WorkforceRuntime",
            status=HealthStatus.HEALTHY,
            details=details,
        )


__all__ = ["WorkforceHealthCheck"]
