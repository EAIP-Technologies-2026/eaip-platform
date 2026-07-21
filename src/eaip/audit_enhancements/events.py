"""Domain events published by the audit enhancements subsystem."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from pydantic import Field

from eaip.audit_enhancements.models import (
    AuditAggregationResult,
    AuditAlertRule,
    AuditCorrelationResult,
    AuditCorrelationRule,
    AuditEnhancementConfig,
    AuditEnhancementReport,
    AuditEnrichmentResult,
    AuditEnrichmentRule,
    AuditStreamConfig,
)
from eaip.events.event import DomainEvent


class AuditCorrelationRuleCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.audit_enhancements.correlation_rule.created"
    rule: AuditCorrelationRule


class AuditCorrelationRuleUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.audit_enhancements.correlation_rule.updated"
    rule_id: str
    changes: dict[str, Any]


class AuditCorrelationRuleDeleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.audit_enhancements.correlation_rule.deleted"
    rule_id: str


class AuditCorrelationDetected(DomainEvent):
    event_type: ClassVar[str] = "eaip.audit_enhancements.correlation.detected"
    result: AuditCorrelationResult


class AuditEnrichmentRuleCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.audit_enhancements.enrichment_rule.created"
    rule: AuditEnrichmentRule


class AuditEnrichmentApplied(DomainEvent):
    event_type: ClassVar[str] = "eaip.audit_enhancements.enrichment.applied"
    result: AuditEnrichmentResult


class AuditAggregationCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.audit_enhancements.aggregation.completed"
    result: AuditAggregationResult


class AuditAlertTriggered(DomainEvent):
    event_type: ClassVar[str] = "eaip.audit_enhancements.alert.triggered"
    alert_rule: AuditAlertRule
    event_id: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class AuditAlertResolved(DomainEvent):
    event_type: ClassVar[str] = "eaip.audit_enhancements.alert.resolved"
    rule_id: str
    resolved_at: datetime
    details: dict[str, Any] = Field(default_factory=dict)


class AuditStreamConfigured(DomainEvent):
    event_type: ClassVar[str] = "eaip.audit_enhancements.stream.configured"
    config: AuditStreamConfig


class AuditStreamStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.audit_enhancements.stream.started"
    stream_id: str


class AuditStreamStopped(DomainEvent):
    event_type: ClassVar[str] = "eaip.audit_enhancements.stream.stopped"
    stream_id: str


class AuditReportGenerated(DomainEvent):
    event_type: ClassVar[str] = "eaip.audit_enhancements.report.generated"
    report: AuditEnhancementReport


class AuditEnhancementConfigUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.audit_enhancements.config.updated"
    config: AuditEnhancementConfig


__all__ = [
    "AuditAggregationCompleted",
    "AuditAlertResolved",
    "AuditAlertTriggered",
    "AuditCorrelationDetected",
    "AuditCorrelationRuleCreated",
    "AuditCorrelationRuleDeleted",
    "AuditCorrelationRuleUpdated",
    "AuditEnhancementConfigUpdated",
    "AuditEnrichmentApplied",
    "AuditEnrichmentRuleCreated",
    "AuditReportGenerated",
    "AuditStreamConfigured",
    "AuditStreamStarted",
    "AuditStreamStopped",
]
