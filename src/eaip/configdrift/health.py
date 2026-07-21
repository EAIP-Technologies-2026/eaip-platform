"""Health check for the configuration drift detection service."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class ConfigDriftHealthCheck:
    name: str = "configdrift"

    async def check(self) -> HealthReport:
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Config drift detector service healthy",
        )


__all__ = ["ConfigDriftHealthCheck"]
