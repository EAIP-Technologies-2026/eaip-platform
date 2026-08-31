"""Data models for dependency scanning — targets, vulnerabilities, results, and config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ScanTargetType(StrEnum):
    """Types of scan targets."""

    LIBRARY = "library"
    PACKAGE = "package"
    CONTAINER = "container"
    INFRASTRUCTURE = "infrastructure"


class Severity(StrEnum):
    """Vulnerability severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ScanTarget(BaseModel):
    """A target to be scanned for vulnerabilities."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    type: ScanTargetType = Field(default=ScanTargetType.LIBRARY)
    location: str
    version: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class Vulnerability(BaseModel):
    """A vulnerability found in a scan target."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    target_id: str
    cve_id: str = Field(default="")
    severity: Severity = Field(default=Severity.MEDIUM)
    description: str = Field(default="")
    fixed_version: str = Field(default="")
    detected_at: datetime = Field(default_factory=utc_now)


class ScanResult(BaseModel):
    """The result of a single scan operation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    scan_id: str
    target_id: str
    started_at: datetime
    completed_at: datetime | None = Field(default=None)
    vulnerabilities: tuple[Vulnerability, ...] = Field(default=())
    total_vulnerabilities: int = Field(default=0, ge=0)
    success: bool = Field(default=True)
    error_message: str = Field(default="")


class ScanConfig(BaseModel):
    """Configuration for the dependency scanner."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True)
    scan_interval_minutes: int = Field(default=1440, ge=1)
    max_concurrent_scans: int = Field(default=3, ge=1)
    fail_on_critical: bool = Field(default=True)
    notify_on_findings: bool = Field(default=True)


__all__ = [
    "ScanConfig",
    "ScanResult",
    "ScanTarget",
    "ScanTargetType",
    "Severity",
    "Vulnerability",
]
