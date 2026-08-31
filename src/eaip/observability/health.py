from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class ObservabilityHealthCheck:
    name: str = "observability"

    def __init__(
        self,
        dashboards_count: int = 0,
        alert_rules_count: int = 0,
        slos_count: int = 0,
    ) -> None:
        self._dashboards_count = dashboards_count
        self._alert_rules_count = alert_rules_count
        self._slos_count = slos_count

    async def check(self) -> HealthReport:
        error_details: list[str] = []

        if self._dashboards_count == 0:
            error_details.append("No dashboards configured")
        if self._alert_rules_count == 0:
            error_details.append("No alert rules configured")
        if self._slos_count == 0:
            error_details.append("No SLOs configured")

        status = HealthStatus.HEALTHY
        if error_details:
            status = HealthStatus.DEGRADED

        return HealthReport(
            component="observability",
            status=status,
            message="; ".join(error_details)
            if error_details
            else "Observability subsystem is operational",
            details={
                "dashboards_total": self._dashboards_count,
                "alert_rules_total": self._alert_rules_count,
                "slos_total": self._slos_count,
            },
        )


__all__ = ["ObservabilityHealthCheck"]
