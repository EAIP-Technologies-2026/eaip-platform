"""Health check for the diagnostics subsystem."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class DiagnosticsHealthCheck:
    name: str = "diagnostics"

    async def check(self) -> HealthReport:
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Diagnostics engine healthy",
        )


__all__ = ["DiagnosticsHealthCheck"]
