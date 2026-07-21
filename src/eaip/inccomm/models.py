"""Data models for incident communication."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class Channel(StrEnum):
    EMAIL = "email"
    SLACK = "slack"
    PAGER_DUTY = "pagerduty"
    SMS = "sms"


class CommStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


class PageStatus(StrEnum):
    INVESTIGATING = "investigating"
    IDENTIFIED = "identified"
    MONITORING = "monitoring"
    RESOLVED = "resolved"


class IncidentComm(BaseModel):
    """A communication sent regarding an incident."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    incident_id: str
    channel: Channel
    subject: str
    body: str
    status: CommStatus = Field(default=CommStatus.PENDING)
    sent_at: datetime | None = Field(default=None)


class StatusPage(BaseModel):
    """A status page update for an incident."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    incident_id: str
    title: str
    message: str
    status: PageStatus = Field(default=PageStatus.INVESTIGATING)
    updated_at: datetime = Field(default_factory=utc_now)


class CommConfig(BaseModel):
    """Configuration for the incident communication tool."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True)
    default_channel: Channel = Field(default=Channel.EMAIL)
    max_retries: int = Field(default=3, ge=0)
    escalation_delay_minutes: int = Field(default=15, ge=1)
    notify_on_resolution: bool = Field(default=True)


__all__ = [
    "Channel",
    "CommConfig",
    "CommStatus",
    "IncidentComm",
    "PageStatus",
    "StatusPage",
]
