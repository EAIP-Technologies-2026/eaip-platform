"""Health check for the enterprise health reporter."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class HealthRptHealthCheck:
    """Health check for the enterprise health reporter."""

    name: str = "healthrpt"

    def __init__(self, component_count: int = 0, report_count: int = 0) -> None:
        self._component_count = component_count
        self._report_count = report_count

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        details = {
            "component_count": self._component_count,
            "report_count": self._report_count,
        }
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message=f"{self._component_count} component(s), {self._report_count} report(s)",
            details=details,
        )


__all__ = ["HealthRptHealthCheck"]
