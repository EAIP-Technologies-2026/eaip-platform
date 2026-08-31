"""Cost data models — records, budgets, alerts, recommendations, reports."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class Category(StrEnum):
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    API = "api"
    AI = "ai"
    OTHER = "other"


class BudgetPeriod(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class BudgetScope(StrEnum):
    TENANT = "tenant"
    WORKFLOW = "workflow"
    AGENT = "agent"
    GLOBAL = "global"


class AlertStatus(StrEnum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class RecommendationType(StrEnum):
    RIGHTSIZE = "rightsize"
    STOP = "stop"
    DELETE = "delete"
    MIGRATE = "migrate"
    COMPRESS = "compress"


class RecommendationEffort(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RecommendationRisk(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RecommendationStatus(StrEnum):
    OPEN = "open"
    APPLIED = "applied"
    DISMISSED = "dismissed"


class CostRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    category: Category
    amount: float
    currency: str
    tenant_id: str | None = None
    workflow_id: str | None = None
    agent_id: str | None = None
    user_id: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    timestamp: datetime = Field(default_factory=utc_now)
    tags: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)
    billed_period_start: datetime | None = None
    billed_period_end: datetime | None = None


class CostBudget(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    category: Category | None = None
    amount: float
    currency: str
    period: BudgetPeriod
    scope: BudgetScope
    scope_id: str | None = None
    start_date: datetime
    end_date: datetime
    alert_thresholds: tuple[float, ...] = Field(default=(0.8, 0.9, 1.0))
    enabled: bool = Field(default=True)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CostAlert(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    budget_id: str
    threshold: float
    actual_spend: float
    budgeted_amount: float
    percentage: float
    status: AlertStatus = Field(default=AlertStatus.ACTIVE)
    triggered_at: datetime = Field(default_factory=utc_now)
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    notified_users: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)


class OptimizationRecommendation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    type: RecommendationType
    resource_type: str
    resource_id: str
    current_cost: float
    estimated_savings: float
    effort: RecommendationEffort
    risk: RecommendationRisk
    description: str
    rationale: str
    status: RecommendationStatus = Field(default=RecommendationStatus.OPEN)
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChargebackItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: str
    tenant_name: str
    category: Category
    amount: float
    percentage: float
    usage_metrics: dict[str, float] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChargebackReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    period_start: datetime
    period_end: datetime
    generated_at: datetime = Field(default_factory=utc_now)
    total_cost: float
    items: tuple[ChargebackItem, ...] = Field(default=())
    currency: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class CostConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    default_currency: str = Field(default="USD")
    enable_budget_alerts: bool = Field(default=True)
    enable_optimization: bool = Field(default=True)
    alert_check_interval_hours: int = Field(default=1)
    data_retention_days: int = Field(default=365)
    exchange_rates: dict[str, float] = Field(default_factory=dict)
