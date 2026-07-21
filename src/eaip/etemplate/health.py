"""Health check for the enterprise template engine."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class TemplateEngineHealthCheck:
    name: str = "etemplate"

    async def check(self) -> HealthReport:
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Template engine healthy",
        )


__all__ = ["TemplateEngineHealthCheck"]
