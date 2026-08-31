"""Data models for the metering and usage service."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class UsagePeriod(StrEnum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class MeteringRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    metric_name: str
    metric_value: float
    timestamp: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class UsageAggregate(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metric_name: str
    tenant_id: str
    period: UsagePeriod
    total_value: float
    count: int = Field(default=0, ge=0)
    average_value: float = Field(default=0.0)
    min_value: float = Field(default=0.0)
    max_value: float = Field(default=0.0)
    period_start: datetime
    period_end: datetime


class MeteringConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    retention_days: int = Field(default=90, ge=1)
    aggregation_interval_minutes: int = Field(default=60, ge=1)
    threshold_warning_pct: float = Field(default=80.0, ge=0.0, le=100.0)
    max_records_per_query: int = Field(default=10000, ge=1)


__all__ = [
    "MeteringConfig",
    "MeteringRecord",
    "UsageAggregate",
    "UsagePeriod",
]
