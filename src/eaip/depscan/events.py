"""Domain events for dependency scanning."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from pydantic import Field

from eaip.depscan.models import Severity
from eaip.events.event import DomainEvent


class ScanStarted(DomainEvent):
    """Emitted when a scan begins."""

    event_type: ClassVar[str] = "eaip.depscan.scan.started"

    scan_id: str
    target_id: str
    started_at: datetime


class ScanCompleted(DomainEvent):
    """Emitted when a scan completes."""

    event_type: ClassVar[str] = "eaip.depscan.scan.completed"

    scan_id: str
    target_id: str
    total_vulnerabilities: int = Field(default=0)
    success: bool = Field(default=True)
    duration_seconds: float = Field(default=0.0)


class VulnerabilityFound(DomainEvent):
    """Emitted when a vulnerability is detected."""

    event_type: ClassVar[str] = "eaip.depscan.vulnerability.found"

    vulnerability_id: str
    target_id: str
    cve_id: str = Field(default="")
    severity: Severity
    description: str = Field(default="")
    details: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "ScanCompleted",
    "ScanStarted",
    "VulnerabilityFound",
]
