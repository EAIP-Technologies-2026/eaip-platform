"""Domain events for runtime diagnostics and self-healing."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class DiagnosticsCheckCompleted(DomainEvent):
    event_type: ClassVar[str] = "diagnostics.check.completed"
    probe_id: str
    status: str
    message: str = ""


class IncidentCreated(DomainEvent):
    event_type: ClassVar[str] = "diagnostics.incident.created"
    incident_id: str
    probe_id: str
    message: str
    severity: str = "warning"


class IncidentResolved(DomainEvent):
    event_type: ClassVar[str] = "diagnostics.incident.resolved"
    incident_id: str
    resolution: str = ""


class AutoRecoveryExecuted(DomainEvent):
    event_type: ClassVar[str] = "diagnostics.recovery.executed"
    recovery_id: str
    target: str
    action: str
    success: bool


__all__ = [
    "AutoRecoveryExecuted",
    "DiagnosticsCheckCompleted",
    "IncidentCreated",
    "IncidentResolved",
]
