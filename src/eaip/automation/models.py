"""Automation domain models - rules, conditions, actions, executions, triggers, and config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class TriggerType(StrEnum):
    EVENT = "event"
    SCHEDULE = "schedule"
    MANUAL = "manual"
    WEBHOOK = "webhook"


class ConditionOperator(StrEnum):
    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    CONTAINS = "contains"
    MATCHES = "matches"
    EXISTS = "exists"


class ActionType(StrEnum):
    WEBHOOK = "webhook"
    WORKFLOW = "workflow"
    AGENT = "agent"
    COMMAND = "command"
    EVENT = "event"
    NOTIFICATION = "notification"


class AutomationStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class LogicOperator(StrEnum):
    AND = "and"
    OR = "or"


class RuleCondition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    field: str
    operator: ConditionOperator
    value: Any = None
    logic: LogicOperator = LogicOperator.AND


class RuleAction(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type: ActionType
    target: str
    payload: dict[str, Any] = Field(default_factory=dict)
    headers: dict[str, str] = Field(default_factory=dict)
    timeout_seconds: float = 30.0
    retry_on_failure: bool = True


class AutomationRule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    trigger_type: TriggerType
    event_pattern: dict[str, Any] | None = None
    schedule_cron: str | None = None
    conditions: tuple[RuleCondition, ...] = Field(default_factory=tuple)
    actions: tuple[RuleAction, ...] = Field(default_factory=tuple)
    enabled: bool = True
    priority: int = 0
    max_retries: int = 3
    timeout_seconds: float = 60.0
    tags: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AutomationExecution(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    rule_id: str
    rule_name: str = ""
    trigger_type: TriggerType
    trigger_event: dict[str, Any] = Field(default_factory=dict)
    status: AutomationStatus = AutomationStatus.PENDING
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    duration_ms: float = 0.0
    result: str = ""
    error: str | None = None
    actions_executed: int = 0
    actions_failed: int = 0
    retry_attempt: int = 0


class TriggerEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    type: str
    source: str
    timestamp: datetime = Field(default_factory=utc_now)
    payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class AutomationConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_concurrent_executions: int = 10
    default_timeout_seconds: float = 60.0
    enable_execution_history: bool = True
    history_retention_days: int = 30
    enable_audit_logging: bool = True
    max_retries_default: int = 3
    cooldown_seconds: float = 1.0


class ExecutionHistoryEntry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    execution_id: str
    rule_id: str
    status: AutomationStatus
    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: float = 0.0
    trigger_type: TriggerType
    result_summary: str = ""
    error_summary: str | None = None


__all__ = [
    "ActionType",
    "AutomationConfig",
    "AutomationExecution",
    "AutomationRule",
    "AutomationStatus",
    "ConditionOperator",
    "ExecutionHistoryEntry",
    "LogicOperator",
    "RuleAction",
    "RuleCondition",
    "TriggerEvent",
    "TriggerType",
]
