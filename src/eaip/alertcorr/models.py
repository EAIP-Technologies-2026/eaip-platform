"""Data models for alert correlation."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class AlertSeverity(StrEnum):
    """Severity levels for alerts."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(StrEnum):
    """Status of an alert."""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class Alert(BaseModel):
    """An individual alert event."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title: str
    description: str = Field(default="")
    severity: AlertSeverity
    status: AlertStatus = Field(default=AlertStatus.OPEN)
    source: str = Field(default="")
    tags: tuple[str, ...] = Field(default=())
    fingerprint: str = Field(default="")
    occurred_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AlertGroup(BaseModel):
    """A group of correlated alerts."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    rule_id: str
    alerts: tuple[Alert, ...] = Field(default=())
    title: str = Field(default="")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CorrelationRule(BaseModel):
    """A rule defining how alerts should be correlated."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = Field(default="")
    match_criteria: dict[str, str] = Field(default_factory=dict)
    group_window_seconds: int = Field(default=300, ge=0)
    enabled: bool = Field(default=True)
    priority: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CorrelationConfig(BaseModel):
    """Configuration for the alert correlator."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    dedup_enabled: bool = Field(default=True)
    suppression_enabled: bool = Field(default=True)
    max_alerts_per_group: int = Field(default=100, ge=1)
    default_group_window_seconds: int = Field(default=300, ge=0)
    max_groups: int = Field(default=1000, ge=1)


__all__ = [
    "Alert",
    "AlertGroup",
    "AlertSeverity",
    "AlertStatus",
    "CorrelationConfig",
    "CorrelationRule",
]
