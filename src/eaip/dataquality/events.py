"""Data quality domain events."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class DataQualityEvent(DomainEvent):
    """Base event for all data quality events."""

    event_type: ClassVar[str] = "eaip.dataquality.event"


class QualityRuleCreated(DataQualityEvent):
    """Published when a quality rule is created."""

    event_type: ClassVar[str] = "eaip.dataquality.rule.created"
    rule_id: str
    name: str
    rule_type: str
    severity: str = "error"


class QualityRuleUpdated(DataQualityEvent):
    """Published when a quality rule is updated."""

    event_type: ClassVar[str] = "eaip.dataquality.rule.updated"
    rule_id: str
    name: str
    changes: dict[str, Any] = Field(default_factory=dict)


class QualityCheckExecuted(DataQualityEvent):
    """Published when a quality check is executed."""

    event_type: ClassVar[str] = "eaip.dataquality.check.executed"
    check_id: str
    status: str
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    duration_ms: float = 0.0


class QualityCheckPassed(DataQualityEvent):
    """Published when a quality check passes."""

    event_type: ClassVar[str] = "eaip.dataquality.check.passed"
    check_id: str
    passed_checks: int = 0


class QualityCheckFailed(DataQualityEvent):
    """Published when a quality check fails."""

    event_type: ClassVar[str] = "eaip.dataquality.check.failed"
    check_id: str
    failed_checks: int = 0
    errors: tuple[str, ...] = ()


class QualityViolationDetected(DataQualityEvent):
    """Published when a quality violation is detected."""

    event_type: ClassVar[str] = "eaip.dataquality.violation.detected"
    violation_id: str
    rule_id: str
    field: str = ""
    severity: str = "error"
    message: str = ""


class AnomalyDetected(DataQualityEvent):
    """Published when an anomaly is detected in data profiling."""

    event_type: ClassVar[str] = "eaip.dataquality.anomaly.detected"
    field: str
    value: Any = None
    score: float = 0.0
    detail: str = ""


__all__ = [
    "AnomalyDetected",
    "DataQualityEvent",
    "QualityCheckExecuted",
    "QualityCheckFailed",
    "QualityCheckPassed",
    "QualityRuleCreated",
    "QualityRuleUpdated",
    "QualityViolationDetected",
]
