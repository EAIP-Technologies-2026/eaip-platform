"""Data models for idle resource notification."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ResourceStatus(StrEnum):
    ACTIVE = "active"
    IDLE = "idle"
    STALE = "stale"
    ARCHIVED = "archived"


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Resource(BaseModel):
    """A tracked resource that may become idle."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    type: str
    last_used_at: datetime
    idle_threshold_hours: int = Field(default=24, ge=1)
    status: ResourceStatus = Field(default=ResourceStatus.ACTIVE)


class IdleNotification(BaseModel):
    """A notification generated for an idle resource."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    resource_id: str
    idle_duration: float = Field(default=0.0, ge=0.0)
    severity: Severity = Field(default=Severity.INFO)
    notified_at: datetime = Field(default_factory=utc_now)
    acknowledged_at: datetime | None = Field(default=None)


class NotifierConfig(BaseModel):
    """Configuration for the idle resource notifier."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True)
    check_interval_minutes: int = Field(default=60, ge=1)
    default_idle_threshold_hours: int = Field(default=24, ge=1)
    notify_on_stale: bool = Field(default=True)
    max_notifications_per_run: int = Field(default=100, ge=1)


__all__ = [
    "IdleNotification",
    "NotifierConfig",
    "Resource",
    "ResourceStatus",
    "Severity",
]
