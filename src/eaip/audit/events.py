"""Domain events published by the audit subsystem."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.audit.models import AuditEvent, AuditPolicy, DataClassification, LegalHold
from eaip.events.event import DomainEvent


class AuditEventLogged(DomainEvent):
    event_type: ClassVar[str] = "audit.event.logged"
    audit_event: AuditEvent


class AuditPolicyCreated(DomainEvent):
    event_type: ClassVar[str] = "audit.policy.created"
    policy: AuditPolicy


class AuditPolicyUpdated(DomainEvent):
    event_type: ClassVar[str] = "audit.policy.updated"
    policy_id: str
    changes: dict[str, Any]


class DataClassified(DomainEvent):
    event_type: ClassVar[str] = "audit.data.classified"
    data_type: str
    classification: DataClassification


class RetentionApplied(DomainEvent):
    event_type: ClassVar[str] = "audit.retention.applied"
    rule_id: str
    data_type: str
    records_affected: int


class LegalHoldCreated(DomainEvent):
    event_type: ClassVar[str] = "audit.legal_hold.created"
    legal_hold: LegalHold


class LegalHoldReleased(DomainEvent):
    event_type: ClassVar[str] = "audit.legal_hold.released"
    legal_hold_id: str
    reason: str


class ComplianceReportGenerated(DomainEvent):
    event_type: ClassVar[str] = "audit.compliance.report.generated"
    framework: str
    status: str
    score: float
    findings_count: int


class AuditStoreCleaned(DomainEvent):
    event_type: ClassVar[str] = "audit.store.cleaned"
    events_removed: int
    remaining: int


class AuditStoreSnapshotCreated(DomainEvent):
    event_type: ClassVar[str] = "audit.store.snapshot.created"
    event_count: int
    snapshot_index: int


__all__ = [
    "AuditEventLogged",
    "AuditPolicyCreated",
    "AuditPolicyUpdated",
    "AuditStoreCleaned",
    "AuditStoreSnapshotCreated",
    "ComplianceReportGenerated",
    "DataClassified",
    "LegalHoldCreated",
    "LegalHoldReleased",
    "RetentionApplied",
]
