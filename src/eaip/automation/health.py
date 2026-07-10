"""Health check for the automation runtime."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus

if TYPE_CHECKING:
    from eaip.automation.engine import AutomationEngine


class AutomationHealthCheck:
    name: str = "automation"

    def __init__(self, engine: AutomationEngine | None = None) -> None:
        from eaip.automation.engine import AutomationEngine

        self._engine = engine or AutomationEngine()

    async def check(self) -> HealthReport:
        error_details: list[str] = []
        rule_count = len(await self._engine.list_rules())
        execution_count = len(self._engine.executions)
        active_count = len(self._engine._active_executions)

        if rule_count == 0:
            error_details.append("No rules registered")

        status = HealthStatus.HEALTHY
        if error_details:
            status = HealthStatus.DEGRADED

        return HealthReport(
            component="automation",
            status=status,
            message="; ".join(error_details) if error_details else "Automation runtime is operational",
            details={
                "rules_registered": rule_count,
                "executions_total": execution_count,
                "executions_active": active_count,
            },
        )


__all__ = ["AutomationHealthCheck"]
