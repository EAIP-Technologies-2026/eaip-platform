"""Cost allocation models — allocations, rules, config."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class CostAllocation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    department: str | None = None
    project: str | None = None
    cost_center: str | None = None
    amount: float
    currency: str
    period_start: datetime
    period_end: datetime
    allocated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AllocationRule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    dimension: str
    criteria: dict[str, Any] = Field(default_factory=dict)
    percentage: float
    enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AllocationConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    default_currency: str = Field(default="USD")
    auto_allocate: bool = Field(default=True)
    allocation_interval_hours: int = Field(default=24)
    data_retention_days: int = Field(default=365)
    rules: tuple[AllocationRule, ...] = Field(default=())
