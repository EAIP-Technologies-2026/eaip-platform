"""Notification orchestration domain models — rules, conditions, actions, schedules, and routing."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class OrchestrationStatus(StrEnum):
    """Status lifecycle for orchestration rules and batches."""

    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DigestFrequency(StrEnum):
    """Frequency options for digest delivery."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    HOURLY = "hourly"
    IMMEDIATE = "immediate"


class RoutePriority(StrEnum):
    """Priority classification for delivery routes."""

    PRIMARY = "primary"
    FALLBACK = "fallback"
    BACKUP = "backup"


class DeliveryRoute(BaseModel):
    """A delivery route specifying channel, priority, and condition."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    channel: str
    priority: RoutePriority = RoutePriority.PRIMARY
    condition: str = ""
    config: dict[str, Any] = Field(default_factory=dict)


class OrchestrationCondition(BaseModel):
    """A condition used to evaluate whether an orchestration rule applies."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    field: str
    operator: str = "eq"
    value: Any = None


class OrchestrationAction(BaseModel):
    """An action to execute when an orchestration rule matches."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: str
    target: str
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EscalationLevel(BaseModel):
    """A single escalation level with delay, channels, and targets."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    level: int = 1
    delay_seconds: float = 300.0
    channels: tuple[str, ...] = Field(default_factory=lambda: ("email",))
    targets: tuple[str, ...] = Field(default_factory=tuple)
    escalate_after: str = ""


class EscalationPolicy(BaseModel):
    """Configuration for escalating notifications through multiple levels."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = True
    max_levels: int = 3
    levels: tuple[EscalationLevel, ...] = Field(default_factory=tuple)
    notify_on_escalation: bool = True
    notify_on_resolve: bool = True


class DigestConfig(BaseModel):
    """Configuration for digest-style notification delivery."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    frequency: DigestFrequency = DigestFrequency.DAILY
    time: str = "08:00"
    timezone: str = "UTC"
    max_items: int = 50
    group_by: str = "channel"
    include_summary: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class OrchestrationSchedule(BaseModel):
    """Cron-based scheduling configuration for orchestration rules."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    cron: str = "0 * * * *"
    timezone: str = "UTC"
    max_executions: int = 0
    cooldown_seconds: float = 0.0


class OrchestrationRule(BaseModel):
    """An orchestration rule defining conditions, actions, routes, and escalation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    status: OrchestrationStatus = OrchestrationStatus.PENDING
    conditions: tuple[OrchestrationCondition, ...] = Field(default_factory=tuple)
    actions: tuple[OrchestrationAction, ...] = Field(default_factory=tuple)
    routes: tuple[DeliveryRoute, ...] = Field(default_factory=tuple)
    schedule: OrchestrationSchedule | None = None
    escalation: EscalationPolicy | None = None
    digest: DigestConfig | None = None
    priority: int = 0
    enabled: bool = True
    tags: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class NotificationOrchestrationConfig(BaseModel):
    """Configuration settings for the notification orchestration engine."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_rules: int = 100
    default_escalation_delay: float = 300.0
    max_escalation_levels: int = 5
    digest_batch_size: int = 50
    enable_history: bool = True
    history_retention_days: int = 30


class NotificationBatch(BaseModel):
    """A batch of notifications processed together for delivery."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    rule_id: str = ""
    notifications: tuple[str, ...] = Field(default_factory=tuple)
    channel: str = ""
    status: OrchestrationStatus = OrchestrationStatus.PENDING
    created_at: datetime = Field(default_factory=utc_now)
    sent_at: datetime | None = None
    error: str | None = None


__all__ = [
    "DeliveryRoute",
    "DigestConfig",
    "DigestFrequency",
    "EscalationLevel",
    "EscalationPolicy",
    "NotificationBatch",
    "NotificationOrchestrationConfig",
    "OrchestrationAction",
    "OrchestrationCondition",
    "OrchestrationRule",
    "OrchestrationSchedule",
    "OrchestrationStatus",
    "RoutePriority",
]
