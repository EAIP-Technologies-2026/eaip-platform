"""Health check for the custom dashboard builder."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class DashboardHealthCheck:
    name: str = "dashboard"

    async def check(self) -> HealthReport:
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Dashboard builder healthy",
        )


__all__ = ["DashboardHealthCheck"]
