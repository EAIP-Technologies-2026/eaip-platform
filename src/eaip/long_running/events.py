"""Domain events for long-running workflows."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from eaip.events.event import DomainEvent
from eaip.long_running.models import (
    WorkflowCheckpoint,
    WorkflowExecutionPlan,
    WorkflowRecoveryStrategy,
    WorkflowState,
    WorkflowStatus,
)


class WorkflowScheduled(DomainEvent):
    event_type: ClassVar[str] = "eaip.long_running.scheduled"
    workflow_id: str = ""
    workflow_name: str = ""
    plan: WorkflowExecutionPlan | None = None
    scheduled_at: datetime | None = None


class WorkflowExecutionStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.long_running.execution.started"
    workflow_id: str = ""
    workflow_name: str = ""
    state: WorkflowState | None = None
    step_id: str = ""


class WorkflowCheckpointCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.long_running.checkpoint.created"
    workflow_id: str = ""
    checkpoint: WorkflowCheckpoint | None = None


class WorkflowCheckpointRestored(DomainEvent):
    event_type: ClassVar[str] = "eaip.long_running.checkpoint.restored"
    workflow_id: str = ""
    checkpoint_id: str = ""
    step_id: str = ""


class WorkflowPausedForDuration(DomainEvent):
    event_type: ClassVar[str] = "eaip.long_running.paused_for_duration"
    workflow_id: str = ""
    workflow_name: str = ""
    duration_seconds: float = 0.0
    resume_at: datetime | None = None


class WorkflowResumedFromCheckpoint(DomainEvent):
    event_type: ClassVar[str] = "eaip.long_running.resumed_from_checkpoint"
    workflow_id: str = ""
    checkpoint_id: str = ""
    step_id: str = ""
    attempt: int = 0


class WorkflowHeartbeatReceived(DomainEvent):
    event_type: ClassVar[str] = "eaip.long_running.heartbeat.received"
    workflow_id: str = ""
    step_id: str = ""
    timestamp: datetime | None = None
    progress: float = 0.0
    payload: dict[str, Any] | None = None


class WorkflowStatePersisted(DomainEvent):
    event_type: ClassVar[str] = "eaip.long_running.state.persisted"
    workflow_id: str = ""
    state: WorkflowState | None = None


class WorkflowStateRecovered(DomainEvent):
    event_type: ClassVar[str] = "eaip.long_running.state.recovered"
    workflow_id: str = ""
    strategy: WorkflowRecoveryStrategy | None = None
    recovered_step_id: str = ""


class WorkflowExecutionCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.long_running.execution.completed"
    workflow_id: str = ""
    workflow_name: str = ""
    status: WorkflowStatus = WorkflowStatus.COMPLETED
    duration_ms: float = 0.0
    result: str = ""
    error: str | None = None


class WorkflowExecutionFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.long_running.execution.failed"
    workflow_id: str = ""
    workflow_name: str = ""
    error: str = ""
    step_id: str = ""
    attempt: int = 0
    will_retry: bool = False


class WorkflowCancelled(DomainEvent):
    event_type: ClassVar[str] = "eaip.long_running.cancelled"
    workflow_id: str = ""
    workflow_name: str = ""
    reason: str = ""
    step_id: str = ""


class WorkflowContinuationTriggered(DomainEvent):
    event_type: ClassVar[str] = "eaip.long_running.continuation.triggered"
    workflow_id: str = ""
    token: str = ""
    next_step_id: str = ""
    context: dict[str, Any] | None = None


__all__ = [
    "WorkflowCancelled",
    "WorkflowCheckpointCreated",
    "WorkflowCheckpointRestored",
    "WorkflowContinuationTriggered",
    "WorkflowExecutionCompleted",
    "WorkflowExecutionFailed",
    "WorkflowExecutionStarted",
    "WorkflowHeartbeatReceived",
    "WorkflowPausedForDuration",
    "WorkflowResumedFromCheckpoint",
    "WorkflowScheduled",
    "WorkflowStatePersisted",
    "WorkflowStateRecovered",
]
