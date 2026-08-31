"""Data quality models — rules, checks, results, violations, config."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class DataQualityConfig(BaseModel):
    """Configuration for data quality subsystem."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    default_severity: Literal["error", "warning", "info"] = Field(default="warning")
    max_violations_per_check: int = Field(default=1000, ge=1, le=100000)
    enable_auto_remediate: bool = Field(default=False)
    retention_days: int = Field(default=90, ge=1, le=3650)
    notify_on_failure: bool = Field(default=True)


class QualityRule(BaseModel):
    """A single data quality rule definition."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = Field(default="")
    field: str
    rule_type: Literal["required", "unique", "range", "pattern", "type", "custom"]
    params: dict[str, Any] = Field(default_factory=dict)
    severity: Literal["error", "warning", "info"] = Field(default="error")
    enabled: bool = Field(default=True)
    tags: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)


class QualityCheck(BaseModel):
    """A scheduled quality check composed of multiple rules."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    rules: tuple[str, ...] = Field(default_factory=tuple)
    schedule_cron: str = Field(default="")
    target: str = Field(default="")
    status: Literal["active", "paused"] = Field(default="active")
    metadata: dict[str, Any] = Field(default_factory=dict)


class QualityResult(BaseModel):
    """The result of executing a quality check."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    check_id: str
    status: Literal["passed", "failed", "error"]
    total_checks: int = Field(default=0, ge=0)
    passed_checks: int = Field(default=0, ge=0)
    failed_checks: int = Field(default=0, ge=0)
    errors: tuple[str, ...] = Field(default_factory=tuple)
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = Field(default=None)
    duration_ms: float = Field(default=0.0, ge=0.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class QualityViolation(BaseModel):
    """A single violation of a quality rule."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    rule_id: str
    record_id: str = Field(default="")
    field: str = Field(default="")
    value: Any = None
    expected: Any = None
    severity: Literal["error", "warning", "info"] = Field(default="error")
    message: str = Field(default="")
    timestamp: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "DataQualityConfig",
    "QualityCheck",
    "QualityResult",
    "QualityRule",
    "QualityViolation",
]
