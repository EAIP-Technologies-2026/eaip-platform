"""Health check for Git integration."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class GitServiceHealthCheck:
    name: str = "gitsvc"

    async def check(self) -> HealthReport:
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Git integration service healthy",
        )


__all__ = ["GitServiceHealthCheck"]
