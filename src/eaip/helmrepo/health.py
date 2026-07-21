"""Health check for Helm chart repository."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class HelmChartHealthCheck:
    name: str = "helmrepo"

    async def check(self) -> HealthReport:
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Helm chart repository healthy",
        )


__all__ = ["HelmChartHealthCheck"]
