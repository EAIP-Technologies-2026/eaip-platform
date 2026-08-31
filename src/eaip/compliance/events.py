"""Domain events for the compliance & regulatory framework."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class ComplianceScanStarted(DomainEvent):
    """Emitted when a compliance scan begins."""

    event_type: ClassVar[str] = "compliance.scan.started"

    regulation_id: str
    scan_id: str


class ComplianceScanCompleted(DomainEvent):
    """Emitted when a compliance scan finishes."""

    event_type: ClassVar[str] = "compliance.scan.completed"

    regulation_id: str
    scan_id: str
    score: float
    status: str


class ControlStatusChanged(DomainEvent):
    """Emitted when a control's compliance status changes."""

    event_type: ClassVar[str] = "compliance.control.status_changed"

    control_id: str
    previous_status: str
    new_status: str


class RemediationCreated(DomainEvent):
    """Emitted when a remediation item is created."""

    event_type: ClassVar[str] = "compliance.remediation.created"

    item_id: str
    control_id: str
    description: str


class RemediationResolved(DomainEvent):
    """Emitted when a remediation item is resolved."""

    event_type: ClassVar[str] = "compliance.remediation.resolved"

    item_id: str
    control_id: str


class EvidenceCollected(DomainEvent):
    """Emitted when evidence is collected for a control."""

    event_type: ClassVar[str] = "compliance.evidence.collected"

    evidence_id: str
    control_id: str
    source: str
