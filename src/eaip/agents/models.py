"""Agent Runtime models — Goal, Step, Plan, AgentSpec, RunRecord."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class StepType(StrEnum):
    """Types of work a step can represent."""

    TOOL_CALL = "tool_call"
    LLM_COMPLETION = "llm_completion"


class RunStatus(StrEnum):
    """Lifecycle status of an agent run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(StrEnum):
    """Execution status of an individual step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Goal(BaseModel):
    """A user-provided goal that an agent should accomplish."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    text: str
    constraints: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Step(BaseModel):
    """A single unit of work within a run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    type: StepType
    tool_name: str = ""
    prompt: str = ""
    input: dict[str, Any] = Field(default_factory=dict)
    output: str = ""
    status: StepStatus = StepStatus.PENDING
    error: str | None = None
    duration_ms: float = 0.0


class Plan(BaseModel):
    """A complete plan produced by a Planner."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    goal: Goal
    steps: tuple[Step, ...]
    reasoning: str = ""


class AgentSpec(BaseModel):
    """Versioned, declarative definition of an agent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    version: str = "0.1.0"
    tools: tuple[str, ...] = Field(default_factory=tuple)
    llm_adapter: str = ""
    max_steps: int = 25
    metadata: dict[str, Any] = Field(default_factory=dict)


class RunRecord(BaseModel):
    """Record of a single agent execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    agent_id: str
    goal: Goal
    plan: Plan | None = None
    status: RunStatus = RunStatus.PENDING
    steps: tuple[Step, ...] = Field(default_factory=tuple)
    result: str = ""
    error: str | None = None
    duration_ms: float = 0.0
    created_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None


__all__ = [
    "AgentSpec",
    "Goal",
    "Plan",
    "RunRecord",
    "RunStatus",
    "Step",
    "StepStatus",
    "StepType",
]
