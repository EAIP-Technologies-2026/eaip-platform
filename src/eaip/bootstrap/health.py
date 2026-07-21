"""Bootstrap health check."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class BootstrapHealthCheck(HealthCheck):
    name: str = "eaip.bootstrap"

    def __init__(
        self,
        available_templates: int = 0,
        total_scaffolds: int = 0,
    ) -> None:
        self._available_templates = available_templates
        self._total_scaffolds = total_scaffolds

    async def check(self) -> HealthReport:
        details = {
            "available_templates": self._available_templates,
            "total_scaffolds": self._total_scaffolds,
        }
        if self._available_templates == 0:
            return HealthReport(
                component="Bootstrap",
                status=HealthStatus.DEGRADED,
                details=details,
                message="no project templates available",
            )
        return HealthReport(
            component="Bootstrap",
            status=HealthStatus.HEALTHY,
            details=details,
        )


__all__ = ["BootstrapHealthCheck"]
