"""Domain events for AI validation."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from eaip.aivalidator.models import RuleCategory
from eaip.events.event import DomainEvent


class ValidationStarted(DomainEvent):
    """Emitted when a validation run begins."""

    event_type: ClassVar[str] = "eaip.aivalidator.validation.started"

    run_id: str
    model_id: str
    rules_count: int = Field(default=0)


class ValidationCompleted(DomainEvent):
    """Emitted when a validation run completes successfully."""

    event_type: ClassVar[str] = "eaip.aivalidator.validation.completed"

    run_id: str
    model_id: str
    overall_score: float = Field(default=0.0)
    passed_rules: int = Field(default=0)
    total_rules: int = Field(default=0)
    duration_seconds: float = Field(default=0.0)


class ValidationFailed(DomainEvent):
    """Emitted when a validation run fails."""

    event_type: ClassVar[str] = "eaip.aivalidator.validation.failed"

    run_id: str
    model_id: str
    reason: str = Field(default="")
    details: dict[str, Any] = Field(default_factory=dict)


class RuleViolated(DomainEvent):
    """Emitted when a validation rule is violated."""

    event_type: ClassVar[str] = "eaip.aivalidator.rule.violated"

    rule_id: str
    rule_name: str
    category: RuleCategory
    metric_value: float = Field(default=0.0)
    threshold: float = Field(default=0.0)
    run_id: str = Field(default="")
    details: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "RuleViolated",
    "ValidationCompleted",
    "ValidationFailed",
    "ValidationStarted",
]
