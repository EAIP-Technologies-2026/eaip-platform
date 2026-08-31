"""Health check for the CI service."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class CIHealthCheck:
    name: str = "ciservice"

    def __init__(self, pipeline_count: int = 0, active_builds: int = 0) -> None:
        self._pipeline_count = pipeline_count
        self._active_builds = active_builds

    async def check(self) -> HealthReport:
        details = {
            "pipeline_count": self._pipeline_count,
            "active_builds": self._active_builds,
        }
        status = HealthStatus.HEALTHY
        message = "CI service is operational"

        if self._pipeline_count == 0:
            status = HealthStatus.DEGRADED
            message = "No pipelines configured"

        return HealthReport(
            component="ciservice",
            status=status,
            message=message,
            details=details,
        )


__all__ = ["CIHealthCheck"]
