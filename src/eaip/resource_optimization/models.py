"""Data models for resource optimization."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ResourceType(StrEnum):
    """Types of resources that can be optimized."""

    COMPUTE = "compute"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"
    GPU = "gpu"
    DATABASE = "database"
    CONTAINER = "container"
    SERVERLESS = "serverless"


class OptimizationStrategy(StrEnum):
    """Strategies for resource optimization."""

    RIGHT_SIZING = "right_sizing"
    SCALE_DOWN = "scale_down"
    SCALE_UP = "scale_up"
    TERMINATE_IDLE = "terminate_idle"
    MIGRATE_INSTANCE = "migrate_instance"
    CHANGE_TIER = "change_tier"
    RESERVED_CAPACITY = "reserved_capacity"
    SPOT_INSTANCE = "spot_instance"


class RecommendationPriority(StrEnum):
    """Priority levels for resource recommendations."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ResourceActionStatus(StrEnum):
    """Status of a resource optimization action."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    SKIPPED = "skipped"


class ResourceOptimizationConfig(BaseModel):
    """Configuration for the resource optimization module."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    auto_apply_recommendations: bool = Field(default=False)
    max_recommendations_per_resource: int = Field(default=10, ge=1)
    utilization_threshold_warning: float = Field(default=70.0, ge=0.0, le=100.0)
    utilization_threshold_critical: float = Field(default=90.0, ge=0.0, le=100.0)
    idle_threshold_hours: int = Field(default=72, ge=1)
    analysis_window_days: int = Field(default=30, ge=1)
    schedule_interval_hours: int = Field(default=24, ge=1)


class ResourceMetrics(BaseModel):
    """Collected metrics for a resource."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    resource_id: str
    resource_type: ResourceType
    cpu_utilization: float = Field(default=0.0, ge=0.0, le=100.0)
    memory_utilization: float = Field(default=0.0, ge=0.0, le=100.0)
    disk_utilization: float = Field(default=0.0, ge=0.0, le=100.0)
    network_in_bytes: int = Field(default=0, ge=0)
    network_out_bytes: int = Field(default=0, ge=0)
    request_count: int = Field(default=0, ge=0)
    error_count: int = Field(default=0, ge=0)
    latency_p99_ms: float = Field(default=0.0, ge=0.0)
    cost_per_hour: float = Field(default=0.0, ge=0.0)
    timestamp: datetime = Field(default_factory=utc_now)
    metadata: dict[str, str] = Field(default_factory=dict)


class ResourceUtilization(BaseModel):
    """Analyzed utilization summary for a resource."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    resource_id: str
    resource_type: ResourceType
    avg_cpu_utilization: float = Field(ge=0.0, le=100.0)
    peak_cpu_utilization: float = Field(ge=0.0, le=100.0)
    avg_memory_utilization: float = Field(ge=0.0, le=100.0)
    peak_memory_utilization: float = Field(ge=0.0, le=100.0)
    avg_disk_utilization: float = Field(ge=0.0, le=100.0)
    is_idle: bool = Field(default=False)
    idle_hours: int = Field(default=0, ge=0)
    period_start: datetime
    period_end: datetime
    data_points: int = Field(default=0, ge=0)


class ResourceOptimizationRule(BaseModel):
    """A rule that triggers optimization recommendations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    resource_type: ResourceType | None = Field(default=None)
    condition_expression: str = ""
    strategy: OptimizationStrategy
    priority: RecommendationPriority = RecommendationPriority.MEDIUM
    enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, str] = Field(default_factory=dict)


class ResourceRecommendation(BaseModel):
    """A recommendation to optimize a resource."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    resource_id: str
    resource_type: ResourceType
    rule_id: str = ""
    strategy: OptimizationStrategy
    priority: RecommendationPriority
    title: str
    description: str = ""
    current_value: str = ""
    recommended_value: str = ""
    estimated_savings_per_hour: float = Field(default=0.0, ge=0.0)
    estimated_savings_per_month: float = Field(default=0.0, ge=0.0)
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=utc_now)
    applied_at: datetime | None = Field(default=None)
    dismissed_at: datetime | None = Field(default=None)
    metadata: dict[str, str] = Field(default_factory=dict)


class ResourceAction(BaseModel):
    """An action taken to optimize a resource."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    recommendation_id: str
    resource_id: str
    resource_type: ResourceType
    action_type: str
    status: ResourceActionStatus = ResourceActionStatus.PENDING
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    error_message: str = ""
    result: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, str] = Field(default_factory=dict)


class ResourceOptimizationReport(BaseModel):
    """A report summarizing optimization analysis."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    period_start: datetime
    period_end: datetime
    total_resources_analyzed: int = Field(default=0, ge=0)
    total_recommendations: int = Field(default=0, ge=0)
    total_estimated_savings_per_month: float = Field(default=0.0, ge=0.0)
    critical_recommendations: int = Field(default=0, ge=0)
    high_recommendations: int = Field(default=0, ge=0)
    medium_recommendations: int = Field(default=0, ge=0)
    low_recommendations: int = Field(default=0, ge=0)
    actions_taken: int = Field(default=0, ge=0)
    actions_failed: int = Field(default=0, ge=0)
    generated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, str] = Field(default_factory=dict)


class ResourceOptimizationSchedule(BaseModel):
    """Schedule configuration for recurring optimization analysis."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    interval_hours: int = Field(default=24, ge=1)
    resource_types: tuple[ResourceType, ...] = Field(default=())
    enabled: bool = Field(default=True)
    auto_apply: bool = Field(default=False)
    last_run_at: datetime | None = Field(default=None)
    next_run_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, str] = Field(default_factory=dict)


class ResourceOptimizationHistory(BaseModel):
    """Historical record of optimization actions."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    resource_id: str
    resource_type: ResourceType
    action_type: str
    strategy: OptimizationStrategy
    status: ResourceActionStatus
    previous_state: str = ""
    new_state: str = ""
    savings_per_hour: float = Field(default=0.0, ge=0.0)
    performed_at: datetime = Field(default_factory=utc_now)
    performed_by: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)


class ResourceAllocation(BaseModel):
    """Current allocation state of a resource."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    resource_id: str
    resource_type: ResourceType
    allocated_capacity: float = Field(default=0.0, ge=0.0)
    used_capacity: float = Field(default=0.0, ge=0.0)
    requested_capacity: float = Field(default=0.0, ge=0.0)
    over_allocated: bool = Field(default=False)
    under_allocated: bool = Field(default=False)
    allocation_efficiency: float = Field(default=0.0, ge=0.0, le=100.0)
    timestamp: datetime = Field(default_factory=utc_now)
    metadata: dict[str, str] = Field(default_factory=dict)


class ResourceDemandForecast(BaseModel):
    """Forecasted demand for a resource."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    resource_id: str
    resource_type: ResourceType
    forecast_horizon_hours: int = Field(default=24, ge=1)
    predicted_cpu_utilization: float = Field(default=0.0, ge=0.0)
    predicted_memory_utilization: float = Field(default=0.0, ge=0.0)
    predicted_demand_trend: str = ""
    confidence_lower: float = Field(default=0.0, ge=0.0)
    confidence_upper: float = Field(default=0.0, ge=0.0)
    generated_at: datetime = Field(default_factory=utc_now)
    valid_until: datetime | None = Field(default=None)
    metadata: dict[str, str] = Field(default_factory=dict)


class ResourceOptimizationDashboard(BaseModel):
    """A dashboard for monitoring resource optimization."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    widgets: tuple[str, ...] = Field(default=())
    resource_ids: tuple[str, ...] = Field(default=())
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, str] = Field(default_factory=dict)


class ResourceConstraint(BaseModel):
    """A constraint that limits optimization options."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    resource_id: str
    resource_type: ResourceType
    constraint_type: str
    constraint_value: str = ""
    description: str = ""
    is_active: bool = Field(default=True)
    detected_at: datetime = Field(default_factory=utc_now)
    resolved_at: datetime | None = Field(default=None)
    metadata: dict[str, str] = Field(default_factory=dict)


class ResourceTag(BaseModel):
    """A tag attached to a resource for classification."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    value: str
    resource_id: str = ""
    resource_type: ResourceType | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)


__all__ = [
    "OptimizationStrategy",
    "RecommendationPriority",
    "ResourceAction",
    "ResourceActionStatus",
    "ResourceAllocation",
    "ResourceConstraint",
    "ResourceDemandForecast",
    "ResourceMetrics",
    "ResourceOptimizationConfig",
    "ResourceOptimizationDashboard",
    "ResourceOptimizationHistory",
    "ResourceOptimizationReport",
    "ResourceOptimizationRule",
    "ResourceOptimizationSchedule",
    "ResourceRecommendation",
    "ResourceTag",
    "ResourceType",
    "ResourceUtilization",
]
