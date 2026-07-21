"""SLA domain events — published via EventBus during SLA lifecycle."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class SlaDefinitionCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.sla_engine.definition.created"
    definition_id: str = ""
    definition_name: str = ""
    target_metric: str = ""


class SlaDefinitionUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.sla_engine.definition.updated"
    definition_id: str = ""
    definition_name: str = ""


class SlaDefinitionDeleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.sla_engine.definition.deleted"
    definition_id: str = ""
    definition_name: str = ""


class SlaMonitorStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.sla_engine.monitor.started"
    monitor_id: str = ""
    definition_id: str = ""


class SlaMonitorCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.sla_engine.monitor.completed"
    monitor_id: str = ""
    definition_id: str = ""
    duration_ms: float = 0.0


class SlaBreached(DomainEvent):
    event_type: ClassVar[str] = "eaip.sla_engine.breached"
    definition_id: str = ""
    definition_name: str = ""
    monitor_id: str = ""
    actual_value: float = 0.0
    threshold: float = 0.0


class SlaWarningTriggered(DomainEvent):
    event_type: ClassVar[str] = "eaip.sla_engine.warning"
    definition_id: str = ""
    definition_name: str = ""
    monitor_id: str = ""
    actual_value: float = 0.0
    threshold: float = 0.0


class SlaViolationLogged(DomainEvent):
    event_type: ClassVar[str] = "eaip.sla_engine.violation.logged"
    violation_id: str = ""
    definition_id: str = ""
    definition_name: str = ""
    metric: str = ""
    actual_value: float = 0.0
    threshold: float = 0.0
    severity: str = "warning"


class SlaStatusUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.sla_engine.status.updated"
    monitor_id: str = ""
    definition_id: str = ""
    previous_status: str = ""
    new_status: str = ""


class SlaPolicyEvaluated(DomainEvent):
    event_type: ClassVar[str] = "eaip.sla_engine.policy.evaluated"
    definition_id: str = ""
    definition_name: str = ""
    monitor_id: str = ""
    current_value: float = 0.0
    breach_detected: bool = False
    warning_detected: bool = False
    details: dict[str, Any] = Field(default_factory=dict)
    violation_ids: tuple[str, ...] = ()


SlaEvent = (
    SlaDefinitionCreated
    | SlaDefinitionUpdated
    | SlaDefinitionDeleted
    | SlaMonitorStarted
    | SlaMonitorCompleted
    | SlaBreached
    | SlaWarningTriggered
    | SlaViolationLogged
    | SlaStatusUpdated
    | SlaPolicyEvaluated
)

__all__ = [
    "SlaBreached",
    "SlaDefinitionCreated",
    "SlaDefinitionDeleted",
    "SlaDefinitionUpdated",
    "SlaEvent",
    "SlaMonitorCompleted",
    "SlaMonitorStarted",
    "SlaPolicyEvaluated",
    "SlaStatusUpdated",
    "SlaViolationLogged",
    "SlaWarningTriggered",
]
