"""Domain events for the BPM engine - lifecycle, activity, gateway, signal, message, timer."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class ProcessDeployed(DomainEvent):
    event_type: ClassVar[str] = "eaip.bpm_engine.process.deployed"
    process_definition_id: str = ""
    process_name: str = ""
    version: int = 0
    key: str = ""


class ProcessStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.bpm_engine.process.started"
    process_instance_id: str = ""
    process_definition_id: str = ""
    process_name: str = ""


class ProcessCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.bpm_engine.process.completed"
    process_instance_id: str = ""
    process_definition_id: str = ""
    process_name: str = ""
    duration_ms: float = 0.0
    completed_activities: int = 0


class ProcessFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.bpm_engine.process.failed"
    process_instance_id: str = ""
    process_definition_id: str = ""
    process_name: str = ""
    error: str = ""
    failed_activity_id: str = ""


class ActivityStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.bpm_engine.activity.started"
    process_instance_id: str = ""
    activity_id: str = ""
    activity_name: str = ""
    activity_type: str = ""
    attempt: int = 0


class ActivityCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.bpm_engine.activity.completed"
    process_instance_id: str = ""
    activity_id: str = ""
    activity_name: str = ""
    activity_type: str = ""
    duration_ms: float = 0.0
    attempt: int = 0


class ActivityFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.bpm_engine.activity.failed"
    process_instance_id: str = ""
    activity_id: str = ""
    activity_name: str = ""
    activity_type: str = ""
    error: str = ""
    attempt: int = 0
    will_retry: bool = False


class GatewayEvaluated(DomainEvent):
    event_type: ClassVar[str] = "eaip.bpm_engine.gateway.evaluated"
    process_instance_id: str = ""
    gateway_id: str = ""
    gateway_name: str = ""
    gateway_type: str = ""
    selected_flow_id: str = ""
    condition_result: bool = False


class SignalReceived(DomainEvent):
    event_type: ClassVar[str] = "eaip.bpm_engine.signal.received"
    process_instance_id: str = ""
    signal_name: str = ""
    signal_payload: dict[str, Any] = Field(default_factory=dict)


class MessageReceived(DomainEvent):
    event_type: ClassVar[str] = "eaip.bpm_engine.message.received"
    process_instance_id: str = ""
    message_name: str = ""
    correlation_key: str = ""
    message_payload: dict[str, Any] = Field(default_factory=dict)


class TimerFired(DomainEvent):
    event_type: ClassVar[str] = "eaip.bpm_engine.timer.fired"
    process_instance_id: str = ""
    activity_id: str = ""
    timer_name: str = ""
    timer_duration_seconds: float = 0.0


class ErrorEventTriggered(DomainEvent):
    event_type: ClassVar[str] = "eaip.bpm_engine.error_event.triggered"
    process_instance_id: str = ""
    error_code: str = ""
    error_message: str = ""
    failed_activity_id: str = ""


BpmEvent = (
    ProcessDeployed
    | ProcessStarted
    | ProcessCompleted
    | ProcessFailed
    | ActivityStarted
    | ActivityCompleted
    | ActivityFailed
    | GatewayEvaluated
    | SignalReceived
    | MessageReceived
    | TimerFired
    | ErrorEventTriggered
)

__all__ = [
    "ActivityCompleted",
    "ActivityFailed",
    "ActivityStarted",
    "BpmEvent",
    "ErrorEventTriggered",
    "GatewayEvaluated",
    "MessageReceived",
    "ProcessCompleted",
    "ProcessDeployed",
    "ProcessFailed",
    "ProcessStarted",
    "SignalReceived",
    "TimerFired",
]
