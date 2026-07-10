"""Workflow domain events — published via EventBus during workflow execution."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.events.event import DomainEvent
from eaip.workflow.models import WorkflowStatus


class WorkflowStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.workflow.started"
    run_id: str = ""
    workflow_id: str = ""
    definition_name: str = ""
    context_keys: tuple[str, ...] = ()
    parent_run_id: str | None = None


class WorkflowStepStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.workflow.step.started"
    run_id: str = ""
    workflow_id: str = ""
    step_id: str = ""
    step_name: str = ""
    agent_id: str = ""
    tool_name: str = ""
    attempt: int = 0
    parallel_group_id: str | None = None


class WorkflowStepCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.workflow.step.completed"
    run_id: str = ""
    workflow_id: str = ""
    step_id: str = ""
    step_name: str = ""
    agent_id: str = ""
    tool_name: str = ""
    attempt: int = 0
    duration_ms: float = 0.0
    output: str = ""


class WorkflowStepFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.workflow.step.failed"
    run_id: str = ""
    workflow_id: str = ""
    step_id: str = ""
    step_name: str = ""
    error: str = ""
    attempt: int = 0
    will_retry: bool = False


class WorkflowStepApprovalRequired(DomainEvent):
    event_type: ClassVar[str] = "eaip.workflow.step.approval_required"
    run_id: str = ""
    workflow_id: str = ""
    step_id: str = ""
    step_name: str = ""
    payload: dict[str, Any] | None = None
    resume_token: str = ""
    approval_prompt: str = ""


class WorkflowStepApproved(DomainEvent):
    event_type: ClassVar[str] = "eaip.workflow.step.approved"
    run_id: str = ""
    workflow_id: str = ""
    step_id: str = ""
    step_name: str = ""
    resume_token: str = ""


class WorkflowStepRejected(DomainEvent):
    event_type: ClassVar[str] = "eaip.workflow.step.rejected"
    run_id: str = ""
    workflow_id: str = ""
    step_id: str = ""
    step_name: str = ""
    reason: str = ""
    resume_token: str = ""


class WorkflowStepSkipped(DomainEvent):
    event_type: ClassVar[str] = "eaip.workflow.step.skipped"
    run_id: str = ""
    workflow_id: str = ""
    step_id: str = ""
    step_name: str = ""


class WorkflowStepTimedOut(DomainEvent):
    event_type: ClassVar[str] = "eaip.workflow.step.timed_out"
    run_id: str = ""
    workflow_id: str = ""
    step_id: str = ""
    step_name: str = ""
    timeout_seconds: float = 0.0


class WorkflowTimedOut(DomainEvent):
    event_type: ClassVar[str] = "eaip.workflow.timed_out"
    run_id: str = ""
    workflow_id: str = ""
    workflow_name: str = ""
    timeout_seconds: float = 0.0
    completed_steps: int = 0


class WorkflowCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.workflow.completed"
    run_id: str = ""
    workflow_id: str = ""
    status: WorkflowStatus = WorkflowStatus.COMPLETED
    duration_ms: float = 0.0
    result: str = ""
    error: str | None = None
    step_count: int = 0
    completed_count: int = 0
    failed_count: int = 0


class WorkflowPaused(DomainEvent):
    event_type: ClassVar[str] = "eaip.workflow.paused"
    run_id: str = ""
    workflow_id: str = ""
    workflow_name: str = ""


class WorkflowResumed(DomainEvent):
    event_type: ClassVar[str] = "eaip.workflow.resumed"
    run_id: str = ""
    workflow_id: str = ""
    workflow_name: str = ""


class WorkflowChildStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.workflow.child.started"
    parent_run_id: str = ""
    child_run_id: str = ""
    workflow_id: str = ""
    workflow_name: str = ""


class WorkflowChildCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.workflow.child.completed"
    parent_run_id: str = ""
    child_run_id: str = ""
    workflow_id: str = ""
    status: WorkflowStatus = WorkflowStatus.COMPLETED
    duration_ms: float = 0.0


class WorkflowParallelGroupStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.workflow.parallel.started"
    run_id: str = ""
    workflow_id: str = ""
    group_id: str = ""
    step_count: int = 0


class WorkflowParallelGroupCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.workflow.parallel.completed"
    run_id: str = ""
    workflow_id: str = ""
    group_id: str = ""
    completed: int = 0
    failed: int = 0
    duration_ms: float = 0.0


WorkflowEvent = (
    WorkflowStarted
    | WorkflowStepStarted
    | WorkflowStepCompleted
    | WorkflowStepFailed
    | WorkflowStepApprovalRequired
    | WorkflowStepApproved
    | WorkflowStepRejected
    | WorkflowStepSkipped
    | WorkflowStepTimedOut
    | WorkflowTimedOut
    | WorkflowCompleted
    | WorkflowPaused
    | WorkflowResumed
    | WorkflowChildStarted
    | WorkflowChildCompleted
    | WorkflowParallelGroupStarted
    | WorkflowParallelGroupCompleted
)


__all__ = [
    "WorkflowChildCompleted",
    "WorkflowChildStarted",
    "WorkflowCompleted",
    "WorkflowEvent",
    "WorkflowParallelGroupCompleted",
    "WorkflowParallelGroupStarted",
    "WorkflowPaused",
    "WorkflowResumed",
    "WorkflowStarted",
    "WorkflowStepApprovalRequired",
    "WorkflowStepApproved",
    "WorkflowStepCompleted",
    "WorkflowStepFailed",
    "WorkflowStepRejected",
    "WorkflowStepSkipped",
    "WorkflowStepStarted",
    "WorkflowStepTimedOut",
    "WorkflowTimedOut",
]
