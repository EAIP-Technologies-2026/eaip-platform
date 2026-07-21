"""Domain events for the data masking module."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from eaip.datamask.models import DataClassificationResult, PiiDetectionResult
from eaip.events.event import DomainEvent


class MaskingRuleCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.datamask.masking_rule.created"
    rule_id: str
    rule_name: str
    data_type: str
    strategy: str


class MaskingRuleUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.datamask.masking_rule.updated"
    rule_id: str
    rule_name: str
    changes: dict[str, Any] = Field(default_factory=dict)


class AnonymizationStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.datamask.anonymization.started"
    job_id: str
    job_name: str
    source: str
    rule_count: int


class AnonymizationCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.datamask.anonymization.completed"
    job_id: str
    job_name: str
    records_processed: int
    records_skipped: int
    duration_ms: float = Field(default=0.0)


class AnonymizationFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.datamask.anonymization.failed"
    job_id: str
    job_name: str
    error: str
    records_processed: int = Field(default=0)


class PiiDetected(DomainEvent):
    event_type: ClassVar[str] = "eaip.datamask.pii.detected"
    result: PiiDetectionResult


class DataClassified(DomainEvent):
    event_type: ClassVar[str] = "eaip.datamask.data.classified"
    result: DataClassificationResult


__all__ = [
    "AnonymizationCompleted",
    "AnonymizationFailed",
    "AnonymizationStarted",
    "DataClassified",
    "MaskingRuleCreated",
    "MaskingRuleUpdated",
    "PiiDetected",
]
