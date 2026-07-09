"""Agent Runtime domain events."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class AgentEvent(DomainEvent):
    """Base event for all Agent Runtime events."""

    event_type: ClassVar[str] = "eaip.agent.event"


class RunStarted(AgentEvent):
    """Published when an agent run starts."""

    event_type: ClassVar[str] = "eaip.agent.run.started"
    run_id: str
    agent_id: str
    goal_text: str


class RunCompleted(AgentEvent):
    """Published when an agent run completes successfully."""

    event_type: ClassVar[str] = "eaip.agent.run.completed"
    run_id: str
    agent_id: str
    step_count: int
    duration_ms: float


class RunFailed(AgentEvent):
    """Published when an agent run fails."""

    event_type: ClassVar[str] = "eaip.agent.run.failed"
    run_id: str
    agent_id: str
    error: str
    step_count: int
    duration_ms: float


class RunCancelled(AgentEvent):
    """Published when an agent run is cancelled."""

    event_type: ClassVar[str] = "eaip.agent.run.cancelled"
    run_id: str
    agent_id: str
    step_count: int


class StepStarted(AgentEvent):
    """Published when a step starts execution."""

    event_type: ClassVar[str] = "eaip.agent.step.started"
    run_id: str
    step_id: str
    step_name: str
    step_type: str


class StepCompleted(AgentEvent):
    """Published when a step completes successfully."""

    event_type: ClassVar[str] = "eaip.agent.step.completed"
    run_id: str
    step_id: str
    step_name: str
    duration_ms: float


class StepFailed(AgentEvent):
    """Published when a step fails."""

    event_type: ClassVar[str] = "eaip.agent.step.failed"
    run_id: str
    step_id: str
    step_name: str
    error: str
    duration_ms: float


__all__ = [
    "AgentEvent",
    "RunCancelled",
    "RunCompleted",
    "RunFailed",
    "RunStarted",
    "StepCompleted",
    "StepFailed",
    "StepStarted",
]
