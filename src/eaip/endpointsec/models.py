"""Data models for endpoint security scanning — endpoints, findings, profiles, and config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class EndpointStatus(StrEnum):
    """Operational status of an endpoint."""

    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class Severity(StrEnum):
    """Finding severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Endpoint(BaseModel):
    """A network endpoint to be scanned."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    host: str
    port: int = Field(ge=1, le=65535)
    protocol: str = Field(default="tcp")
    tags: dict[str, str] = Field(default_factory=dict)
    status: EndpointStatus = Field(default=EndpointStatus.UNKNOWN)
    last_seen: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)


class ScanFinding(BaseModel):
    """A security finding discovered during an endpoint scan."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    endpoint_id: str
    severity: Severity = Field(default=Severity.INFO)
    cve_id: str = Field(default="")
    description: str = Field(default="")
    remediation: str = Field(default="")
    detected_at: datetime = Field(default_factory=utc_now)
    resolved_at: datetime | None = Field(default=None)


class ScanProfile(BaseModel):
    """A named scan profile defining what checks to perform."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    checks: tuple[str, ...] = Field(default=())
    timeout_seconds: int = Field(default=30, ge=1)
    enabled: bool = Field(default=True)


class ScanConfig(BaseModel):
    """Configuration for the endpoint security scanner."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True)
    scan_interval_minutes: int = Field(default=60, ge=1)
    max_concurrent_scans: int = Field(default=5, ge=1)
    default_profile_id: str = Field(default="default")
    notify_on_critical: bool = Field(default=True)


__all__ = [
    "Endpoint",
    "EndpointStatus",
    "ScanConfig",
    "ScanFinding",
    "ScanProfile",
    "Severity",
]
