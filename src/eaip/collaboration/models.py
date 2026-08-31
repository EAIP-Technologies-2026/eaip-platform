"""Collaboration domain models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class SessionType(StrEnum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    BROADCAST = "broadcast"
    AUCTION = "auction"


class SessionStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStatus(StrEnum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class DelegationStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"


class CoordinationStrategy(StrEnum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    BROADCAST = "broadcast"
    AUCTION = "auction"
    CONSENSUS = "consensus"


class ErrorStrategy(StrEnum):
    ABORT = "abort"
    CONTINUE = "continue"
    ISOLATION = "isolation"


class CollaborationSession(BaseModel):
    """A multi-agent collaboration session."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    type: SessionType
    status: SessionStatus = SessionStatus.PENDING
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    agents: tuple[str, ...] = Field(default_factory=tuple)
    coordinator_agent_id: str = ""
    context: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    max_rounds: int = 1
    timeout_seconds: float = 0.0


class AgentTask(BaseModel):
    """A task assigned to an agent within a collaboration session."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    session_id: str
    agent_id: str
    task_type: str = ""
    description: str = ""
    input_data: dict[str, Any] = Field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 0
    assigned_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    output: str = ""
    error: str | None = None
    duration_ms: float = 0.0
    depends_on: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DelegationRequest(BaseModel):
    """A request to delegate a task from one agent to another."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    from_agent_id: str
    to_agent_id: str
    task_description: str = ""
    context: dict[str, Any] = Field(default_factory=dict)
    priority: int = 0
    deadline: datetime | None = None
    status: DelegationStatus = DelegationStatus.PENDING
    response: str = ""
    created_at: datetime = Field(default_factory=utc_now)


class CoordinationConfig(BaseModel):
    """Configuration for collaboration coordination strategy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy: CoordinationStrategy = CoordinationStrategy.SEQUENTIAL
    max_rounds: int = 1
    timeout_seconds: float = 0.0
    require_consensus: bool = False
    consensus_threshold: float = 1.0
    error_strategy: ErrorStrategy = ErrorStrategy.ABORT


class CollaborationResult(BaseModel):
    """Outcome of a collaboration session execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    session_id: str
    status: SessionStatus
    task_results: tuple[AgentTask, ...] = Field(default_factory=tuple)
    agent_count: int = 0
    total_duration_ms: float = 0.0
    consensus_reached: bool = False
    output_summary: str = ""


class SharedState(BaseModel):
    """Shared mutable state for a collaboration session."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    session_id: str
    variables: dict[str, Any] = Field(default_factory=dict)
    agent_contributions: dict[str, str] = Field(default_factory=dict)
    version: int = 1
    updated_at: datetime = Field(default_factory=utc_now)


__all__ = [
    "AgentTask",
    "CollaborationResult",
    "CollaborationSession",
    "CoordinationConfig",
    "CoordinationStrategy",
    "DelegationRequest",
    "DelegationStatus",
    "ErrorStrategy",
    "SessionStatus",
    "SessionType",
    "SharedState",
    "TaskStatus",
]
