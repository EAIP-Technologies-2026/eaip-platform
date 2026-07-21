"""Alert service — threshold-based cost alerts."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from eaip.cost.exceptions import AlertNotFoundError
from eaip.cost.models import AlertStatus, CostAlert, CostBudget


class AlertService:
    """Manages cost alerts triggered by budget thresholds."""

    def __init__(self) -> None:
        self._alerts: dict[str, CostAlert] = {}
        self._event_callback: Callable[..., Any] | None = None
        self._alert_counter: int = 0

    def set_event_callback(self, callback: Callable[..., Any]) -> None:
        self._event_callback = callback

    async def _emit(self, event: Any) -> None:
        if self._event_callback is not None:
            await self._event_callback(event)

    async def check_and_alert(
        self,
        budget: CostBudget,
        current_spend: float,
        percentage: float,
        threshold: float,
    ) -> dict[str, Any] | None:
        # avoid duplicate active alerts for the same budget+threshold
        for alert in self._alerts.values():
            if (
                alert.budget_id == budget.id
                and alert.threshold == threshold
                and alert.status is AlertStatus.ACTIVE
            ):
                return None
        self._alert_counter += 1
        alert = CostAlert(
            id=f"alert-{self._alert_counter}",
            budget_id=budget.id,
            threshold=threshold,
            actual_spend=current_spend,
            budgeted_amount=budget.amount,
            percentage=percentage,
            status=AlertStatus.ACTIVE,
        )
        self._alerts[alert.id] = alert
        if self._event_callback is not None:
            from eaip.cost.events import AlertCreated

            await self._event_callback(
                AlertCreated(
                    alert_id=alert.id,
                    budget_id=budget.id,
                    threshold=threshold,
                    actual_spend=current_spend,
                    percentage=percentage,
                )
            )
        return {
            "alert_id": alert.id,
            "budget_id": budget.id,
            "threshold": threshold,
            "actual_spend": current_spend,
            "percentage": percentage,
        }

    async def acknowledge_alert(self, alert_id: str) -> CostAlert:
        if alert_id not in self._alerts:
            raise AlertNotFoundError(f"Alert {alert_id} not found")
        alert = self._alerts[alert_id]
        updated = CostAlert(
            id=alert.id,
            budget_id=alert.budget_id,
            threshold=alert.threshold,
            actual_spend=alert.actual_spend,
            budgeted_amount=alert.budgeted_amount,
            percentage=alert.percentage,
            status=AlertStatus.ACKNOWLEDGED,
            triggered_at=alert.triggered_at,
            acknowledged_at=datetime.now(alert.triggered_at.tzinfo),
            resolved_at=alert.resolved_at,
            notified_users=alert.notified_users,
            metadata=alert.metadata,
        )
        self._alerts[alert_id] = updated
        if self._event_callback is not None:
            from eaip.cost.events import AlertAcknowledged

            acknowledged_at = updated.acknowledged_at or datetime.now()
            await self._event_callback(
                AlertAcknowledged(alert_id=alert_id, acknowledged_at=acknowledged_at)
            )
        return updated

    async def resolve_alert(self, alert_id: str) -> CostAlert:
        if alert_id not in self._alerts:
            raise AlertNotFoundError(f"Alert {alert_id} not found")
        alert = self._alerts[alert_id]
        updated = CostAlert(
            id=alert.id,
            budget_id=alert.budget_id,
            threshold=alert.threshold,
            actual_spend=alert.actual_spend,
            budgeted_amount=alert.budgeted_amount,
            percentage=alert.percentage,
            status=AlertStatus.RESOLVED,
            triggered_at=alert.triggered_at,
            acknowledged_at=alert.acknowledged_at,
            resolved_at=alert.triggered_at or datetime.now(),
            notified_users=alert.notified_users,
            metadata=alert.metadata,
        )
        self._alerts[alert_id] = updated
        if self._event_callback is not None:
            from eaip.cost.events import AlertResolved

            resolved_at = updated.resolved_at or datetime.now()
            await self._event_callback(AlertResolved(alert_id=alert_id, resolved_at=resolved_at))
        return updated

    async def list_alerts(
        self,
        budget_id: str | None = None,
        status: str | None = None,
    ) -> list[CostAlert]:
        results = list(self._alerts.values())
        if budget_id is not None:
            results = [a for a in results if a.budget_id == budget_id]
        if status is not None:
            results = [a for a in results if a.status.value == status]
        return results
