"""Domain events for the cost intelligence engine."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class CostRecorded(DomainEvent):
    event_type: ClassVar[str] = "eaip.cost.recorded"

    record_id: str
    category: str
    amount: float
    currency: str
    tenant_id: str | None = None
    workflow_id: str | None = None
    agent_id: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None


class BudgetCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.cost.budget.created"

    budget_id: str
    name: str
    amount: float
    currency: str
    period: str
    scope: str
    scope_id: str | None = None


class BudgetUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.cost.budget.updated"

    budget_id: str
    updates: dict[str, Any] = Field(default_factory=dict)


class BudgetThresholdReached(DomainEvent):
    event_type: ClassVar[str] = "eaip.cost.budget.threshold_reached"

    budget_id: str
    threshold: float
    actual_spend: float
    budgeted_amount: float
    percentage: float


class BudgetExceeded(DomainEvent):
    event_type: ClassVar[str] = "eaip.cost.budget.exceeded"

    budget_id: str
    actual_spend: float
    budgeted_amount: float
    overshoot: float


class AlertCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.cost.alert.created"

    alert_id: str
    budget_id: str
    threshold: float
    actual_spend: float
    percentage: float


class AlertAcknowledged(DomainEvent):
    event_type: ClassVar[str] = "eaip.cost.alert.acknowledged"

    alert_id: str
    acknowledged_at: datetime


class AlertResolved(DomainEvent):
    event_type: ClassVar[str] = "eaip.cost.alert.resolved"

    alert_id: str
    resolved_at: datetime


class RecommendationGenerated(DomainEvent):
    event_type: ClassVar[str] = "eaip.cost.recommendation.generated"

    recommendation_id: str
    type: str
    resource_type: str
    resource_id: str
    estimated_savings: float


class RecommendationApplied(DomainEvent):
    event_type: ClassVar[str] = "eaip.cost.recommendation.applied"

    recommendation_id: str
    type: str
    resource_id: str


class ChargebackGenerated(DomainEvent):
    event_type: ClassVar[str] = "eaip.cost.chargeback.generated"

    report_id: str
    period_start: datetime
    period_end: datetime
    total_cost: float
    item_count: int
