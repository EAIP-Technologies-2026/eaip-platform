"""Script runtime health check."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class ScriptHealthCheck(HealthCheck):
    name: str = "eaip.script"

    def __init__(
        self,
        registered_functions: int = 0,
        active_executions: int = 0,
        failed_executions: int = 0,
        timed_out_executions: int = 0,
    ) -> None:
        self._registered_functions = registered_functions
        self._active_executions = active_executions
        self._failed_executions = failed_executions
        self._timed_out_executions = timed_out_executions

    async def check(self) -> HealthReport:
        details = {
            "registered_functions": self._registered_functions,
            "active_executions": self._active_executions,
            "failed_executions": self._failed_executions,
            "timed_out_executions": self._timed_out_executions,
        }
        if self._timed_out_executions > 0:
            return HealthReport(
                component="ScriptRuntime",
                status=HealthStatus.DEGRADED,
                details=details,
                message=f"{self._timed_out_executions} timed out execution(s) detected",
            )
        if self._failed_executions > 5:
            return HealthReport(
                component="ScriptRuntime",
                status=HealthStatus.DEGRADED,
                details=details,
                message=f"{self._failed_executions} failed execution(s) detected",
            )
        if self._active_executions == 0 and self._registered_functions == 0:
            return HealthReport(
                component="ScriptRuntime",
                status=HealthStatus.HEALTHY,
                details=details,
                message="no functions registered",
            )
        return HealthReport(
            component="ScriptRuntime",
            status=HealthStatus.HEALTHY,
            details=details,
        )


__all__ = ["ScriptHealthCheck"]
