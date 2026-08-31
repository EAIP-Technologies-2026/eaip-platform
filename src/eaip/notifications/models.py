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
    ACKNOWLEDGED = "acknowledged"
    DISMISSED = "dismissed"


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


class NotificationSeverity(StrEnum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationCategory(StrEnum):
    SYSTEM = "system"
    SECURITY = "security"
    OPERATIONS = "operations"
    APPROVALS = "approvals"
    AUTOMATION = "automation"
    WORKFLOW = "workflow"
    DEPLOYMENT = "deployment"
    KNOWLEDGE = "knowledge"
    CONDUCTOR = "conductor"


class Notification(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    type: str
    channel: NotificationChannel
    priority: NotificationPriority = NotificationPriority.NORMAL
    severity: NotificationSeverity = NotificationSeverity.INFO
    category: NotificationCategory = NotificationCategory.SYSTEM
    recipients: tuple[str, ...]
    subject: str
    body: str = ""
    summary: str = ""
    template_id: str | None = None
    template_variables: dict[str, Any] = Field(default_factory=dict)
    status: NotificationStatus = NotificationStatus.PENDING
    created_at: datetime = Field(default_factory=utc_now)
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    read_at: datetime | None = None
    acknowledged_at: datetime | None = None
    dismissed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = None
    tenant_id: str | None = None
    organization_id: str | None = None
    source: str = ""
    deep_link: str | None = None
    related_entity_id: str | None = None
    related_entity_type: str | None = None
    group_key: str | None = None


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
    "NotificationCategory",
    "NotificationChannel",
    "NotificationConfig",
    "NotificationPreference",
    "NotificationPriority",
    "NotificationSeverity",
    "NotificationStatus",
    "NotificationTemplate",
]
