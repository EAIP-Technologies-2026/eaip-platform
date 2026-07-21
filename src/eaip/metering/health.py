"""Health check for the metering and usage service."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class MeteringHealthCheck:
    name: str = "metering"

    async def check(self) -> HealthReport:
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Metering service healthy",
        )


__all__ = ["MeteringHealthCheck"]
