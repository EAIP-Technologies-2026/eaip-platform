"""Job health check — reports scheduler and executor health."""

from __future__ import annotations

from typing import Any

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class JobHealthCheck(HealthCheck):
    name: str = "eaip.jobs"

    def __init__(
        self,
        scheduler: Any = None,
        executor: Any = None,
    ) -> None:
        self._scheduler = scheduler
        self._executor = executor

    async def check(self) -> HealthReport:
        details: dict[str, object] = {}
        if self._scheduler is not None:
            details["definitions"] = len(self._scheduler.list_definitions())
        if self._executor is not None:
            total_runs = 0
            active_runs = 0
            for job in self._executor._jobs.values():
                runs = job.list_runs()
                total_runs += len(runs)
                active_runs += sum(
                    1 for r in runs if r.status in ("running", "pending")
                )
            details["total_runs"] = total_runs
            details["active_runs"] = active_runs

        return HealthReport(
            component="jobs",
            status=HealthStatus.HEALTHY,
            message="Job subsystem running",
            details=details,
        )


__all__ = ["JobHealthCheck"]
