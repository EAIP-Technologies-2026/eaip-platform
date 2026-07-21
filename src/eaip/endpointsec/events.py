"""Domain events for endpoint security scanning."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from eaip.endpointsec.models import Severity
from eaip.events.event import DomainEvent


class EndpointRegistered(DomainEvent):
    """Emitted when a new endpoint is registered."""

    event_type: ClassVar[str] = "eaip.endpointsec.endpoint.registered"

    endpoint_id: str
    name: str
    host: str
    port: int
    tags: dict[str, str] = Field(default_factory=dict)


class ScanCompleted(DomainEvent):
    """Emitted when a scan completes."""

    event_type: ClassVar[str] = "eaip.endpointsec.scan.completed"

    endpoint_id: str
    scan_id: str
    total_findings: int = Field(default=0)
    critical_count: int = Field(default=0)
    success: bool = Field(default=True)
    duration_seconds: float = Field(default=0.0)


class FindingReported(DomainEvent):
    """Emitted when a new finding is reported."""

    event_type: ClassVar[str] = "eaip.endpointsec.finding.reported"

    finding_id: str
    endpoint_id: str
    severity: Severity
    cve_id: str = Field(default="")
    description: str = Field(default="")
    details: dict[str, Any] = Field(default_factory=dict)


class FindingResolved(DomainEvent):
    """Emitted when a finding is marked as resolved."""

    event_type: ClassVar[str] = "eaip.endpointsec.finding.resolved"

    finding_id: str
    endpoint_id: str
    severity: Severity


__all__ = [
    "EndpointRegistered",
    "FindingReported",
    "FindingResolved",
    "ScanCompleted",
]
