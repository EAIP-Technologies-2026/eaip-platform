"""AI Cost models — config, records, budgets, alerts, optimization, reports, dashboards."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class CostType(StrEnum):
    PROMPT = "prompt"
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    FINE_TUNE = "fine_tune"
    CACHE_HIT = "cache_hit"
    INFERENCE = "inference"
    TRAINING = "training"
    TOTAL = "total"


class BudgetPeriod(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class OptimizationStrategy(StrEnum):
    MODEL_SWITCH = "model_switch"
    CACHE_OPTIMIZE = "cache_optimize"
    BATCH_INFERENCE = "batch_inference"
    PROMPT_COMPRESSION = "prompt_compression"
    RETRY_POLICY = "retry_policy"
    TIER_DOWNGRADE = "tier_downgrade"


class AiCostReportPeriod(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    CUSTOM = "custom"


class AiCostConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    default_currency: str = Field(default="USD")
    enable_budget_alerts: bool = Field(default=True)
    enable_optimization: bool = Field(default=True)
    enable_projections: bool = Field(default=True)
    alert_check_interval_hours: int = Field(default=1)
    data_retention_days: int = Field(default=365)
    projection_horizon_days: int = Field(default=90)
    exchange_rates: dict[str, float] = Field(default_factory=dict)


class ModelCostRate(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    model_id: str
    provider: str
    input_cost_per_1k_tokens: float
    output_cost_per_1k_tokens: float
    currency: str = Field(default="USD")
    effective_from: datetime = Field(default_factory=utc_now)
    effective_to: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TokenCostBreakdown(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    input_tokens: int = Field(default=0)
    output_tokens: int = Field(default=0)
    input_cost: float = Field(default=0.0)
    output_cost: float = Field(default=0.0)
    currency: str = Field(default="USD")


class AiCostRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    model_id: str
    cost_type: CostType
    amount: float
    currency: str = Field(default="USD")
    tenant_id: str | None = None
    workflow_id: str | None = None
    agent_id: str | None = None
    user_id: str | None = None
    input_tokens: int = Field(default=0)
    output_tokens: int = Field(default=0)
    timestamp: datetime = Field(default_factory=utc_now)
    tags: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)
    token_breakdown: TokenCostBreakdown | None = None


class AiCostBudget(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    model_id: str | None = None
    cost_type: CostType | None = None
    amount: float
    currency: str = Field(default="USD")
    period: BudgetPeriod
    start_date: datetime
    end_date: datetime
    alert_thresholds: tuple[float, ...] = Field(default=(0.8, 0.9, 1.0))
    enabled: bool = Field(default=True)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AiCostAlert(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    budget_id: str
    threshold: float
    actual_spend: float
    budgeted_amount: float
    percentage: float
    triggered_at: datetime = Field(default_factory=utc_now)
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    notified_users: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)


class AiCostOptimizationRule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    strategy: OptimizationStrategy
    model_id: str | None = None
    condition: dict[str, Any] = Field(default_factory=dict)
    action: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AiCostReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    period: AiCostReportPeriod
    period_start: datetime
    period_end: datetime
    generated_at: datetime = Field(default_factory=utc_now)
    total_cost: float
    cost_by_model: dict[str, float] = Field(default_factory=dict)
    cost_by_type: dict[str, float] = Field(default_factory=dict)
    cost_by_tenant: dict[str, float] = Field(default_factory=dict)
    total_input_tokens: int = Field(default=0)
    total_output_tokens: int = Field(default=0)
    currency: str = Field(default="USD")
    metadata: dict[str, Any] = Field(default_factory=dict)


class AiCostAllocation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    department: str | None = None
    project: str | None = None
    cost_center: str | None = None
    model_id: str | None = None
    amount: float
    currency: str = Field(default="USD")
    period_start: datetime
    period_end: datetime
    allocated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AiCostProjection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    model_id: str | None = None
    projected_amount: float
    confidence_interval_low: float
    confidence_interval_high: float
    projection_start: datetime
    projection_end: datetime
    computed_at: datetime = Field(default_factory=utc_now)
    historical_data_points: int = Field(default=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AiCostDashboard(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    current_spend: float = Field(default=0.0)
    budget_remaining: float = Field(default=0.0)
    projected_cost: float = Field(default=0.0)
    savings_from_optimization: float = Field(default=0.0)
    last_updated: datetime = Field(default_factory=utc_now)
    top_models: tuple[str, ...] = Field(default=())
    active_alerts: int = Field(default=0)
    currency: str = Field(default="USD")
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "AiCostAlert",
    "AiCostAllocation",
    "AiCostBudget",
    "AiCostConfig",
    "AiCostDashboard",
    "AiCostOptimizationRule",
    "AiCostProjection",
    "AiCostRecord",
    "AiCostReport",
    "AiCostReportPeriod",
    "BudgetPeriod",
    "CostType",
    "ModelCostRate",
    "OptimizationStrategy",
    "TokenCostBreakdown",
]
