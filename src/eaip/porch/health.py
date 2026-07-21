"""Health check for the pipeline orchestration engine."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class PorchHealthCheck:
    name: str = "porch"

    async def check(self) -> HealthReport:
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Pipeline orchestration engine healthy",
        )


__all__ = ["PorchHealthCheck"]
