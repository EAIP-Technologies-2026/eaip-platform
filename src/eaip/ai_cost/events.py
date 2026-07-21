"""Domain events for the AI cost optimization service."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class AiCostRecorded(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_cost.recorded"

    record_id: str
    model_id: str
    cost_type: str
    amount: float
    currency: str
    tenant_id: str | None = None
    workflow_id: str | None = None
    agent_id: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0


class AiCostBudgetCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_cost.budget.created"

    budget_id: str
    name: str
    amount: float
    currency: str
    period: str
    model_id: str | None = None


class AiCostBudgetUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_cost.budget.updated"

    budget_id: str
    updates: dict[str, Any] = Field(default_factory=dict)


class AiCostBudgetExceeded(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_cost.budget.exceeded"

    budget_id: str
    actual_spend: float
    budgeted_amount: float
    overshoot: float


class AiCostBudgetAlertTriggered(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_cost.budget.alert_triggered"

    alert_id: str
    budget_id: str
    threshold: float
    actual_spend: float
    percentage: float


class AiCostOptimizationRuleCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_cost.optimization_rule.created"

    rule_id: str
    name: str
    strategy: str
    model_id: str | None = None


class AiCostOptimizationApplied(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_cost.optimization_applied"

    rule_id: str
    model_id: str
    estimated_savings: float
    currency: str


class AiCostReportGenerated(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_cost.report.generated"

    report_id: str
    period: str
    period_start: datetime
    period_end: datetime
    total_cost: float


class AiCostProjectionComputed(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_cost.projection.computed"

    projection_id: str
    model_id: str | None = None
    projected_amount: float
    projection_start: datetime
    projection_end: datetime


class AiCostAllocationUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_cost.allocation.updated"

    allocation_id: str
    tenant_id: str
    amount: float
    currency: str
    period_start: datetime
    period_end: datetime


class AiCostDashboardUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_cost.dashboard.updated"

    dashboard_id: str
    current_spend: float
    projected_cost: float
    active_alerts: int


class ModelCostRateUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_cost.model_cost_rate.updated"

    model_id: str
    provider: str
    input_cost_per_1k_tokens: float
    output_cost_per_1k_tokens: float
    currency: str


class AiCostAnomalyDetected(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_cost.anomaly.detected"

    model_id: str
    actual_cost: float
    expected_cost: float
    deviation: float
    severity: str


AiCostEvent = (
    AiCostRecorded
    | AiCostBudgetCreated
    | AiCostBudgetUpdated
    | AiCostBudgetExceeded
    | AiCostBudgetAlertTriggered
    | AiCostOptimizationRuleCreated
    | AiCostOptimizationApplied
    | AiCostReportGenerated
    | AiCostProjectionComputed
    | AiCostAllocationUpdated
    | AiCostDashboardUpdated
    | ModelCostRateUpdated
    | AiCostAnomalyDetected
)


__all__ = [
    "AiCostAllocationUpdated",
    "AiCostAnomalyDetected",
    "AiCostBudgetAlertTriggered",
    "AiCostBudgetCreated",
    "AiCostBudgetExceeded",
    "AiCostBudgetUpdated",
    "AiCostDashboardUpdated",
    "AiCostEvent",
    "AiCostOptimizationApplied",
    "AiCostOptimizationRuleCreated",
    "AiCostProjectionComputed",
    "AiCostRecorded",
    "AiCostReportGenerated",
    "ModelCostRateUpdated",
]
