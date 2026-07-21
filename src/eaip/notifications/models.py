"""Notification domain models — notification, template, preference, delivery record, and config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class NotificationStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"


class NotificationChannel(StrEnum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class NotificationPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Notification(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    type: str
    channel: NotificationChannel
    priority: NotificationPriority = NotificationPriority.NORMAL
    recipients: tuple[str, ...]
    subject: str
    body: str = ""
    template_id: str | None = None
    template_variables: dict[str, Any] = Field(default_factory=dict)
    status: NotificationStatus = NotificationStatus.PENDING
    created_at: datetime = Field(default_factory=utc_now)
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    read_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = None


class NotificationTemplate(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    channel: NotificationChannel
    subject_template: str
    body_template: str = ""
    variables: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)


class NotificationPreference(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    user_id: str
    channel: NotificationChannel
    enabled: bool = True
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    max_daily: int | None = None


class DeliveryRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    notification_id: str
    channel: NotificationChannel
    recipient: str
    status: NotificationStatus
    attempt: int = 1
    error: str | None = None
    timestamp: datetime = Field(default_factory=utc_now)
    duration_ms: float | None = None
    provider_response: dict[str, Any] = Field(default_factory=dict)


class NotificationConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    default_priority: NotificationPriority = NotificationPriority.NORMAL
    max_retries: int = 3
    retry_delay_seconds: int = 60
    enable_digest: bool = False
    digest_interval_minutes: int = 60
    channel_providers: dict[str, str] = Field(default_factory=dict)


__all__ = [
    "DeliveryRecord",
    "Notification",
    "NotificationChannel",
    "NotificationConfig",
    "NotificationPreference",
    "NotificationPriority",
    "NotificationStatus",
    "NotificationTemplate",
]
