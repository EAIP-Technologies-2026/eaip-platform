"""AiCostHealthCheck — reports AI cost optimization service health."""

from __future__ import annotations

from eaip.ai_cost.service import AiCostService
from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class AiCostHealthCheck(HealthCheck):
    """Reports AI cost subsystem health based on records, budgets, and alerts."""

    name: str = "eaip.ai_cost"

    def __init__(self, service: AiCostService | None = None) -> None:
        self._service = service or AiCostService()

    async def check(self) -> HealthReport:
        records = await self._service.query_costs()
        budgets = await self._service.list_budgets()
        rules = await self._service.list_optimization_rules()

        record_count = len(records)
        budget_count = len(budgets)
        rule_count = len(rules)

        details = {
            "record_count": record_count,
            "budget_count": budget_count,
            "optimization_rule_count": rule_count,
            "retention_days": self._service.config.data_retention_days,
            "projections_enabled": self._service.config.enable_projections,
        }

        if record_count == 0:
            return HealthReport(
                component="AiCostService",
                status=HealthStatus.DEGRADED,
                details=details,
                message="no cost records registered",
            )

        return HealthReport(
            component="AiCostService",
            status=HealthStatus.HEALTHY,
            details=details,
        )


__all__ = ["AiCostHealthCheck"]
