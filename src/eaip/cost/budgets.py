"""Budget management — create, update, check budgets against cost data."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from typing import Any

from eaip.cost.alerts import AlertService
from eaip.cost.exceptions import BudgetNotFoundError
from eaip.cost.models import CostBudget
from eaip.cost.tracker import CostTracker


class BudgetManager:
    """Manages cost budgets and checks them against actual spend."""

    def __init__(self, tracker: CostTracker, alert_service: AlertService | None = None) -> None:
        self._tracker = tracker
        self._alert_service = alert_service or AlertService()
        self._budgets: dict[str, CostBudget] = {}
        self._event_callback: Callable[..., Any] | None = None

    def set_event_callback(self, callback: Callable[..., Any]) -> None:
        self._event_callback = callback

    async def _emit(self, event: Any) -> None:
        if self._event_callback is not None:
            await self._event_callback(event)

    async def create_budget(self, budget: CostBudget) -> CostBudget:
        self._budgets[budget.id] = budget
        if self._event_callback is not None:
            from eaip.cost.events import BudgetCreated

            await self._event_callback(
                BudgetCreated(
                    budget_id=budget.id,
                    name=budget.name,
                    amount=budget.amount,
                    currency=budget.currency,
                    period=budget.period.value,
                    scope=budget.scope.value,
                    scope_id=budget.scope_id,
                )
            )
        return budget

    async def update_budget(self, budget_id: str, updates: dict[str, Any]) -> CostBudget:
        if budget_id not in self._budgets:
            raise BudgetNotFoundError(f"Budget {budget_id} not found")
        current = self._budgets[budget_id]
        updated_data = dict(deepcopy(current.__dict__))
        for key, value in updates.items():
            if key in updated_data:
                updated_data[key] = value
        updated = CostBudget(**updated_data)
        self._budgets[budget_id] = updated
        if self._event_callback is not None:
            from eaip.cost.events import BudgetUpdated

            await self._event_callback(BudgetUpdated(budget_id=budget_id, updates=updates))
        return updated

    async def get_budget(self, budget_id: str) -> CostBudget:
        if budget_id not in self._budgets:
            raise BudgetNotFoundError(f"Budget {budget_id} not found")
        return self._budgets[budget_id]

    async def delete_budget(self, budget_id: str) -> None:
        if budget_id not in self._budgets:
            raise BudgetNotFoundError(f"Budget {budget_id} not found")
        del self._budgets[budget_id]

    async def list_budgets(
        self,
        scope: str | None = None,
        category: str | None = None,
    ) -> list[CostBudget]:
        results = list(self._budgets.values())
        if scope is not None:
            results = [b for b in results if b.scope.value == scope]
        if category is not None:
            results = [
                b for b in results if b.category is not None and b.category.value == category
            ]
        return results

    async def check_budgets(self) -> list[dict[str, Any]]:
        triggered: list[dict[str, Any]] = []
        for budget in self._budgets.values():
            if not budget.enabled:
                continue
            current_spend = await self._tracker.get_total_cost(
                scope=budget.scope.value,
                scope_id=budget.scope_id,
            )
            if budget.amount <= 0:
                continue
            percentage = current_spend / budget.amount
            for threshold in budget.alert_thresholds:
                if percentage >= threshold:
                    result = await self._alert_service.check_and_alert(
                        budget, current_spend, percentage, threshold
                    )
                    if result is not None:
                        triggered.append(result)
                        if self._event_callback is not None:
                            from eaip.cost.events import BudgetThresholdReached

                            await self._event_callback(
                                BudgetThresholdReached(
                                    budget_id=budget.id,
                                    threshold=threshold,
                                    actual_spend=current_spend,
                                    budgeted_amount=budget.amount,
                                    percentage=percentage,
                                )
                            )
                        if percentage >= 1.0 and self._event_callback is not None:
                            from eaip.cost.events import BudgetExceeded

                            await self._event_callback(
                                BudgetExceeded(
                                    budget_id=budget.id,
                                    actual_spend=current_spend,
                                    budgeted_amount=budget.amount,
                                    overshoot=current_spend - budget.amount,
                                )
                            )
        return triggered

    async def get_budget_status(self, budget_id: str) -> dict[str, Any]:
        budget = await self.get_budget(budget_id)
        current_spend = await self._tracker.get_total_cost(
            scope=budget.scope.value,
            scope_id=budget.scope_id,
        )
        percentage = current_spend / budget.amount if budget.amount > 0 else 0.0
        alerts = await self._alert_service.list_alerts(budget_id=budget_id)
        return {
            "budget": budget,
            "current_spend": current_spend,
            "budgeted_amount": budget.amount,
            "percentage": percentage,
            "remaining": max(0.0, budget.amount - current_spend),
            "active_alerts": len([a for a in alerts if a.status.value == "active"]),
            "total_alerts": len(alerts),
        }
