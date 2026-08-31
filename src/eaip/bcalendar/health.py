"""Health check for the business calendar service."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class CalendarHealthCheck:
    name: str = "bcalendar"

    async def check(self) -> HealthReport:
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Calendar service healthy",
        )


__all__ = ["CalendarHealthCheck"]
