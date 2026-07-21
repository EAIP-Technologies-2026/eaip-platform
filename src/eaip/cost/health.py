"""Health check for the cost intelligence engine."""

from __future__ import annotations

from eaip.cost.alerts import AlertService
from eaip.cost.budgets import BudgetManager
from eaip.cost.tracker import CostTracker
from eaip.health.checks import HealthReport, HealthStatus


class CostHealthCheck:
    """Health check for cost engine components.

    Implements the :class:`eaip.health.checks.HealthCheck` protocol.
    """

    name: str = "cost"

    def __init__(
        self,
        tracker: CostTracker,
        budget_manager: BudgetManager,
        alert_service: AlertService,
    ) -> None:
        self._tracker = tracker
        self._budget_manager = budget_manager
        self._alert_service = alert_service

    async def check(self) -> HealthReport:
        details: dict[str, object] = {}
        try:
            budgets = await self._budget_manager.list_budgets()
            details["budget_count"] = len(budgets)
        except Exception as exc:
            return HealthReport(
                component=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Budget manager unavailable: {exc}",
                details={"error": str(exc)},
            )
        try:
            alerts = await self._alert_service.list_alerts()
            active_alerts = [a for a in alerts if a.status.value == "active"]
            details["alert_count"] = len(alerts)
            details["active_alert_count"] = len(active_alerts)
        except Exception as exc:
            details["alert_error"] = str(exc)
        try:
            records = await self._tracker.query_costs()
            details["record_count"] = len(records)
        except Exception as exc:
            details["tracker_error"] = str(exc)

        status = HealthStatus.HEALTHY
        messages: list[str] = []
        alert_count = details.get("active_alert_count", 0)
        if isinstance(alert_count, (int, float)) and alert_count > 0:
            status = HealthStatus.DEGRADED
            messages.append(f"{details['active_alert_count']} active alert(s)")

        return HealthReport(
            component=self.name,
            status=status,
            message="; ".join(messages) if messages else "Cost engine healthy",
            details=details,
        )
