"""Domain events for the automation runtime."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from eaip.automation.models import (
    AutomationExecution,
    AutomationRule,
    AutomationStatus,
    RuleAction,
)
from eaip.events.event import DomainEvent


class RuleRegistered(DomainEvent):
    event_type: ClassVar[str] = "automation.rule.registered"
    rule: AutomationRule


class RuleUnregistered(DomainEvent):
    event_type: ClassVar[str] = "automation.rule.unregistered"
    rule_id: str
    rule_name: str


class RuleUpdated(DomainEvent):
    event_type: ClassVar[str] = "automation.rule.updated"
    rule: AutomationRule


class RuleTriggered(DomainEvent):
    event_type: ClassVar[str] = "automation.rule.triggered"
    rule_id: str
    rule_name: str
    trigger_type: str
    trigger_event: dict[str, Any]


class RuleExecutionStarted(DomainEvent):
    event_type: ClassVar[str] = "automation.rule.execution.started"
    execution: AutomationExecution


class RuleExecutionCompleted(DomainEvent):
    event_type: ClassVar[str] = "automation.rule.execution.completed"
    execution: AutomationExecution


class RuleExecutionFailed(DomainEvent):
    event_type: ClassVar[str] = "automation.rule.execution.failed"
    execution: AutomationExecution
    error: str


class ActionExecuted(DomainEvent):
    event_type: ClassVar[str] = "automation.action.executed"
    execution_id: str
    action: RuleAction
    result: str
    duration_ms: float


class ActionFailed(DomainEvent):
    event_type: ClassVar[str] = "automation.action.failed"
    execution_id: str
    action: RuleAction
    error: str
    attempt: int


class ConditionEvaluated(DomainEvent):
    event_type: ClassVar[str] = "automation.condition.evaluated"
    rule_id: str
    execution_id: str
    result: bool
    evaluated_at: datetime


class ScheduleTriggered(DomainEvent):
    event_type: ClassVar[str] = "automation.schedule.triggered"
    rule_id: str
    cron_expression: str


__all__ = [
    "ActionExecuted",
    "ActionFailed",
    "ConditionEvaluated",
    "RuleExecutionCompleted",
    "RuleExecutionFailed",
    "RuleExecutionStarted",
    "RuleRegistered",
    "RuleTriggered",
    "RuleUnregistered",
    "RuleUpdated",
    "ScheduleTriggered",
]
