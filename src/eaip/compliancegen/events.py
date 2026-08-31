"""Domain events emitted by the compliance report generator."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class ScanStarted(DomainEvent):
    """Emitted when a compliance scan begins."""

    event_type: ClassVar[str] = "eaip.compliancegen.scan_started"

    scan_id: str
    framework_id: str
    target: str


class ScanCompleted(DomainEvent):
    """Emitted when a compliance scan finishes."""

    event_type: ClassVar[str] = "eaip.compliancegen.scan_completed"

    scan_id: str
    finding_count: int
    passed: int
    failed: int
    warnings: int


class FindingReported(DomainEvent):
    """Emitted when a compliance finding is reported."""

    event_type: ClassVar[str] = "eaip.compliancegen.finding_reported"

    finding_id: str
    scan_id: str
    control_id: str
    status: str
