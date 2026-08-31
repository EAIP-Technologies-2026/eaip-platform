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


# ── Agent lifecycle events ────────────────────────────────────────


class AgentCreated(AgentEvent):
    """Published when a new agent definition is created."""

    event_type: ClassVar[str] = "eaip.agent.created"
    agent_id: str
    name: str
    version: str = ""


class AgentUpdated(AgentEvent):
    """Published when an agent definition is updated."""

    event_type: ClassVar[str] = "eaip.agent.updated"
    agent_id: str
    name: str
    changes: tuple[str, ...] = ()


class AgentStarted(AgentEvent):
    """Published when an agent begins execution."""

    event_type: ClassVar[str] = "eaip.agent.started"
    agent_id: str
    run_id: str


class AgentPaused(AgentEvent):
    """Published when an agent execution is paused."""

    event_type: ClassVar[str] = "eaip.agent.paused"
    agent_id: str
    run_id: str


class AgentStopped(AgentEvent):
    """Published when an agent execution is stopped."""

    event_type: ClassVar[str] = "eaip.agent.stopped"
    agent_id: str
    run_id: str


class AgentFailed(AgentEvent):
    """Published when an agent execution fails."""

    event_type: ClassVar[str] = "eaip.agent.failed"
    agent_id: str
    run_id: str
    error: str


class AgentDeleted(AgentEvent):
    """Published when an agent definition is deleted."""

    event_type: ClassVar[str] = "eaip.agent.deleted"
    agent_id: str
    name: str


class AgentExecuted(AgentEvent):
    """Published after an agent completes a run."""

    event_type: ClassVar[str] = "eaip.agent.executed"
    agent_id: str
    run_id: str
    duration_ms: float
    step_count: int
    success: bool


__all__ = [
    "AgentCreated",
    "AgentDeleted",
    "AgentEvent",
    "AgentExecuted",
    "AgentFailed",
    "AgentPaused",
    "AgentStarted",
    "AgentStopped",
    "AgentUpdated",
    "RunCancelled",
    "RunCompleted",
    "RunFailed",
    "RunStarted",
    "StepCompleted",
    "StepFailed",
    "StepStarted",
]
