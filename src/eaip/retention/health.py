"""Health check for the data retention and purge service."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class RetentionHealthCheck:
    name: str = "retention"

    async def check(self) -> HealthReport:
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Retention service healthy",
        )


__all__ = ["RetentionHealthCheck"]
