"""Domain events for resource optimization."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent
from eaip.resource_optimization.models import (
    OptimizationStrategy,
    RecommendationPriority,
    ResourceType,
)


class ResourceOptimizationConfigUpdated(DomainEvent):
    """Emitted when the resource optimization configuration is updated."""

    event_type: ClassVar[str] = "eaip.resource_optimization.config.updated"

    changes: dict[str, str | float | bool | int]


class ResourceMetricsCollected(DomainEvent):
    """Emitted when resource metrics are collected."""

    event_type: ClassVar[str] = "eaip.resource_optimization.metrics.collected"

    metrics_id: str
    resource_id: str
    resource_type: ResourceType
    cpu_utilization: float
    memory_utilization: float


class ResourceUtilizationAnalyzed(DomainEvent):
    """Emitted when resource utilization is analyzed."""

    event_type: ClassVar[str] = "eaip.resource_optimization.utilization.analyzed"

    resource_id: str
    resource_type: ResourceType
    avg_cpu_utilization: float
    avg_memory_utilization: float
    is_idle: bool


class ResourceOptimizationRuleCreated(DomainEvent):
    """Emitted when an optimization rule is created."""

    event_type: ClassVar[str] = "eaip.resource_optimization.rule.created"

    rule_id: str
    name: str
    strategy: OptimizationStrategy


class ResourceOptimizationRuleUpdated(DomainEvent):
    """Emitted when an optimization rule is updated."""

    event_type: ClassVar[str] = "eaip.resource_optimization.rule.updated"

    rule_id: str
    name: str
    changes: dict[str, str | float | bool | int]


class ResourceOptimizationRuleDeleted(DomainEvent):
    """Emitted when an optimization rule is deleted."""

    event_type: ClassVar[str] = "eaip.resource_optimization.rule.deleted"

    rule_id: str
    name: str


class ResourceRecommendationGenerated(DomainEvent):
    """Emitted when a resource recommendation is generated."""

    event_type: ClassVar[str] = "eaip.resource_optimization.recommendation.generated"

    recommendation_id: str
    resource_id: str
    resource_type: ResourceType
    strategy: OptimizationStrategy
    priority: RecommendationPriority
    estimated_savings_per_month: float


class ResourceRecommendationApplied(DomainEvent):
    """Emitted when a resource recommendation is applied."""

    event_type: ClassVar[str] = "eaip.resource_optimization.recommendation.applied"

    recommendation_id: str
    resource_id: str
    action_id: str


class ResourceRecommendationDismissed(DomainEvent):
    """Emitted when a resource recommendation is dismissed."""

    event_type: ClassVar[str] = "eaip.resource_optimization.recommendation.dismissed"

    recommendation_id: str
    resource_id: str
    reason: str = ""


class ResourceActionStarted(DomainEvent):
    """Emitted when a resource optimization action starts."""

    event_type: ClassVar[str] = "eaip.resource_optimization.action.started"

    action_id: str
    recommendation_id: str
    resource_id: str
    action_type: str


class ResourceActionCompleted(DomainEvent):
    """Emitted when a resource optimization action completes successfully."""

    event_type: ClassVar[str] = "eaip.resource_optimization.action.completed"

    action_id: str
    recommendation_id: str
    resource_id: str
    result: dict[str, str]


class ResourceActionFailed(DomainEvent):
    """Emitted when a resource optimization action fails."""

    event_type: ClassVar[str] = "eaip.resource_optimization.action.failed"

    action_id: str
    recommendation_id: str
    resource_id: str
    error_message: str


class ResourceOptimizationReportGenerated(DomainEvent):
    """Emitted when an optimization report is generated."""

    event_type: ClassVar[str] = "eaip.resource_optimization.report.generated"

    report_id: str
    total_recommendations: int
    total_estimated_savings_per_month: float


class ResourceDemandForecastComputed(DomainEvent):
    """Emitted when a resource demand forecast is computed."""

    event_type: ClassVar[str] = "eaip.resource_optimization.forecast.computed"

    forecast_id: str
    resource_id: str
    resource_type: ResourceType
    predicted_cpu_utilization: float
    predicted_memory_utilization: float


class ResourceConstraintDetected(DomainEvent):
    """Emitted when a resource constraint is detected."""

    event_type: ClassVar[str] = "eaip.resource_optimization.constraint.detected"

    constraint_id: str
    resource_id: str
    resource_type: ResourceType
    constraint_type: str


class ResourceOptimizationDashboardUpdated(DomainEvent):
    """Emitted when an optimization dashboard is updated."""

    event_type: ClassVar[str] = "eaip.resource_optimization.dashboard.updated"

    dashboard_id: str
    name: str


class ResourceAllocationAdjusted(DomainEvent):
    """Emitted when a resource allocation is adjusted."""

    event_type: ClassVar[str] = "eaip.resource_optimization.allocation.adjusted"

    allocation_id: str
    resource_id: str
    resource_type: ResourceType
    previous_capacity: float
    new_capacity: float


__all__ = [
    "ResourceActionCompleted",
    "ResourceActionFailed",
    "ResourceActionStarted",
    "ResourceAllocationAdjusted",
    "ResourceConstraintDetected",
    "ResourceDemandForecastComputed",
    "ResourceMetricsCollected",
    "ResourceOptimizationConfigUpdated",
    "ResourceOptimizationDashboardUpdated",
    "ResourceOptimizationReportGenerated",
    "ResourceOptimizationRuleCreated",
    "ResourceOptimizationRuleDeleted",
    "ResourceOptimizationRuleUpdated",
    "ResourceRecommendationApplied",
    "ResourceRecommendationDismissed",
    "ResourceRecommendationGenerated",
    "ResourceUtilizationAnalyzed",
]
