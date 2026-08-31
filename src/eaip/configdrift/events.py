"""Domain events for the configuration drift detection service."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class SnapshotCaptured(DomainEvent):
    event_type: ClassVar[str] = "eaip.configdrift.snapshot.captured"

    snapshot_id: str
    resource_id: str


class DriftDetected(DomainEvent):
    event_type: ClassVar[str] = "eaip.configdrift.drift.detected"

    report_id: str
    resource_id: str
    baseline_id: str
    current_id: str
    differences_count: int
    severity: str


class DriftResolved(DomainEvent):
    event_type: ClassVar[str] = "eaip.configdrift.drift.resolved"

    report_id: str
    resource_id: str


__all__ = [
    "DriftDetected",
    "DriftResolved",
    "SnapshotCaptured",
]
