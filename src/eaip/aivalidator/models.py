"""Data models for AI validation — rules, runs, results, and config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class RuleCategory(StrEnum):
    """Categories of validation rules."""

    FAIRNESS = "fairness"
    BIAS = "bias"
    ACCURACY = "accuracy"
    ROBUSTNESS = "robustness"
    SAFETY = "safety"


class ValidationRunStatus(StrEnum):
    """Status of a validation run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ValidationRule(BaseModel):
    """A single validation rule applied during a validation run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    category: RuleCategory = Field(default=RuleCategory.SAFETY)
    metric: str
    threshold: float = Field(default=0.0)
    enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now)


class ValidationResult(BaseModel):
    """The result of applying a single validation rule."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    rule_name: str
    passed: bool = Field(default=True)
    metric_value: float = Field(default=0.0)
    threshold: float = Field(default=0.0)
    details: dict[str, Any] = Field(default_factory=dict)


class ValidationRun(BaseModel):
    """A complete validation run against a model."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    model_id: str
    rules_applied: tuple[str, ...] = Field(default=())
    results: tuple[ValidationResult, ...] = Field(default=())
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    status: ValidationRunStatus = Field(default=ValidationRunStatus.PENDING)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)

    @property
    def duration_seconds(self) -> float | None:
        if self.started_at is not None and self.completed_at is not None:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class ValidatorConfig(BaseModel):
    """Configuration for the AI validator."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True)
    max_parallel_rules: int = Field(default=4, ge=1)
    fail_fast: bool = Field(default=False)
    min_overall_score: float = Field(default=0.7, ge=0.0, le=1.0)
    notify_on_failure: bool = Field(default=True)


__all__ = [
    "RuleCategory",
    "ValidationResult",
    "ValidationRule",
    "ValidationRun",
    "ValidationRunStatus",
    "ValidatorConfig",
]
