"""Workflow domain models - Workflow, WorkflowDefinition, WorkflowRun, WorkflowStep, WorkflowEdge, WorkflowStatus, WorkflowResult, WorkflowContext."""  # noqa: E501

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class WorkflowStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class WorkflowStepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"
    WAITING_APPROVAL = "waiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMED_OUT = "timed_out"


class EdgeCondition(StrEnum):
    """Condition type for workflow edges (routing)."""

    ALWAYS = "always"
    ON_SUCCESS = "on_success"
    ON_FAILURE = "on_failure"
    ON_COMPLETE = "on_complete"
    EXPRESSION = "expression"


class WorkflowEdge(BaseModel):
    """A directed edge between two workflow steps."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source_id: str
    target_id: str
    condition: EdgeCondition = EdgeCondition.ALWAYS
    expression: str = ""
    label: str = ""


class RetryPolicy(BaseModel):
    """Retry policy for a workflow step."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_attempts: int = 3
    delay_seconds: float = 1.0
    backoff_multiplier: float = 2.0
    max_delay_seconds: float = 60.0
    jitter: float = 0.0


class TimeoutConfig(BaseModel):
    """Timeout configuration for workflow execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    workflow_timeout_seconds: float = 0.0
    step_timeout_seconds: float = 0.0
    approval_timeout_seconds: float = 3600.0


class ParallelGroup(BaseModel):
    """A group of steps that execute in parallel."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    step_ids: tuple[str, ...] = Field(default_factory=tuple)
    completion_condition: str = "all"  # "all", "any", "n_of"
    required_count: int = 0  # for "n_of" condition
    timeout_seconds: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class DurableExecutionConfig(BaseModel):
    """Configuration for durable workflow execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = False
    store_type: str = "memory"
    persist_after_each_step: bool = True
    recovery_strategy: str = "restart"  # "restart", "resume", "skip_completed"


class ParentChildConfig(BaseModel):
    """Configuration for parent/child workflow relationships."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    propagate_failure: bool = True
    propagate_cancellation: bool = True
    inherit_context: bool = True
    wait_for_completion: bool = True


class WorkflowStep(BaseModel):
    """A single step within a workflow definition."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    agent_id: str = ""
    tool_name: str = ""
    prompt: str = ""
    input: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: float = 0.0
    retry_policy: RetryPolicy | None = None
    requires_approval: bool = False
    approval_prompt: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowDefinition(BaseModel):
    """A reusable workflow template/definition."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    version: str = "0.1.0"
    steps: tuple[WorkflowStep, ...] = Field(default_factory=tuple)
    edges: tuple[WorkflowEdge, ...] = Field(default_factory=tuple)
    parallel_groups: tuple[ParallelGroup, ...] = Field(default_factory=tuple)
    entry_point: str = ""
    timeout_config: TimeoutConfig | None = None
    durable_config: DurableExecutionConfig | None = None
    parent_child_config: ParentChildConfig | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowStepRecord(BaseModel):
    """Execution record for a single workflow step."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    step_id: str
    name: str
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING
    agent_id: str = ""
    tool_name: str = ""
    prompt: str = ""
    input: dict[str, Any] = Field(default_factory=dict)
    output: str = ""
    error: str | None = None
    attempt: int = 0
    duration_ms: float = 0.0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    approval_token: str | None = None
    parallel_group_id: str | None = None


class WorkflowRun(BaseModel):
    """Runtime record for a single workflow execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    workflow_id: str
    definition: WorkflowDefinition
    status: WorkflowStatus = WorkflowStatus.PENDING
    steps: tuple[WorkflowStepRecord, ...] = Field(default_factory=tuple)
    context: dict[str, Any] = Field(default_factory=dict)
    result: str = ""
    error: str | None = None
    duration_ms: float = 0.0
    resume_token: str | None = None
    parent_run_id: str | None = None
    child_run_ids: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=utc_now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    durable_state: dict[str, Any] = Field(default_factory=dict)
    state_machine_state: str = "pending"


class WorkflowResult(BaseModel):
    """Outcome of a workflow execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    run_id: str
    workflow_id: str
    status: WorkflowStatus
    result: str = ""
    error: str | None = None
    step_count: int = 0
    completed_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    timed_out_count: int = 0
    duration_ms: float = 0.0
    child_results: tuple[WorkflowResult, ...] = Field(default_factory=tuple)


class WorkflowContext(BaseModel):
    """Mutable context shared across workflow steps during execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    variables: dict[str, Any] = Field(default_factory=dict)
    agent_outputs: dict[str, str] = Field(default_factory=dict)
    tool_outputs: dict[str, str] = Field(default_factory=dict)
    shared_memory_keys: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.variables.get(key, default)

    def set(self, key: str, value: Any) -> WorkflowContext:
        return WorkflowContext(
            variables={**self.variables, key: value},
            agent_outputs=self.agent_outputs,
            tool_outputs=self.tool_outputs,
            shared_memory_keys=self.shared_memory_keys,
            metadata=self.metadata,
        )

    def add_agent_output(self, step_id: str, output: str) -> WorkflowContext:
        return WorkflowContext(
            variables=self.variables,
            agent_outputs={**self.agent_outputs, step_id: output},
            tool_outputs=self.tool_outputs,
            shared_memory_keys=self.shared_memory_keys,
            metadata=self.metadata,
        )

    def add_tool_output(self, step_id: str, output: str) -> WorkflowContext:
        return WorkflowContext(
            variables=self.variables,
            agent_outputs=self.agent_outputs,
            tool_outputs={**self.tool_outputs, step_id: output},
            shared_memory_keys=self.shared_memory_keys,
            metadata=self.metadata,
        )

    def add_memory_key(self, key: str) -> WorkflowContext:
        return WorkflowContext(
            variables=self.variables,
            agent_outputs=self.agent_outputs,
            tool_outputs=self.tool_outputs,
            shared_memory_keys=tuple({*self.shared_memory_keys, key}),
            metadata=self.metadata,
        )


__all__ = [
    "DurableExecutionConfig", "EdgeCondition", "ParallelGroup",
    "ParentChildConfig", "RetryPolicy", "TimeoutConfig",
    "WorkflowContext", "WorkflowDefinition", "WorkflowEdge",
    "WorkflowResult", "WorkflowRun", "WorkflowStatus",
    "WorkflowStep", "WorkflowStepRecord", "WorkflowStepStatus",
]
