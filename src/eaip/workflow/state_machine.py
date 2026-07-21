"""Workflow State Machine — finite state machine for workflow run lifecycle."""

from __future__ import annotations

from enum import StrEnum


class WorkflowState(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class StepState(StrEnum):
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


_WORKFLOW_TRANSITIONS: dict[WorkflowState, set[WorkflowState]] = {
    WorkflowState.PENDING: {WorkflowState.RUNNING, WorkflowState.CANCELLED},
    WorkflowState.RUNNING: {
        WorkflowState.COMPLETED,
        WorkflowState.FAILED,
        WorkflowState.CANCELLED,
        WorkflowState.PAUSED,
        WorkflowState.WAITING_APPROVAL,
        WorkflowState.TIMED_OUT,
    },
    WorkflowState.PAUSED: {WorkflowState.RUNNING, WorkflowState.CANCELLED},
    WorkflowState.WAITING_APPROVAL: {
        WorkflowState.RUNNING,
        WorkflowState.FAILED,
        WorkflowState.CANCELLED,
    },
    WorkflowState.COMPLETED: set(),
    WorkflowState.FAILED: set(),
    WorkflowState.CANCELLED: set(),
    WorkflowState.TIMED_OUT: set(),
}

_STEP_TRANSITIONS: dict[StepState, set[StepState]] = {
    StepState.PENDING: {StepState.RUNNING, StepState.SKIPPED, StepState.BLOCKED},
    StepState.RUNNING: {
        StepState.COMPLETED,
        StepState.FAILED,
        StepState.WAITING_APPROVAL,
        StepState.TIMED_OUT,
    },
    StepState.COMPLETED: set(),
    StepState.FAILED: set(),
    StepState.SKIPPED: set(),
    StepState.BLOCKED: {StepState.PENDING, StepState.RUNNING},
    StepState.WAITING_APPROVAL: {StepState.APPROVED, StepState.REJECTED, StepState.TIMED_OUT},
    StepState.APPROVED: {StepState.RUNNING},
    StepState.REJECTED: {StepState.FAILED},
    StepState.TIMED_OUT: set(),
}


class WorkflowStateMachine:
    """Finite state machine for workflow run lifecycle.

    Enforces valid transitions and provides query methods
    for determining workflow state behaviour.
    """

    def __init__(self, initial: WorkflowState = WorkflowState.PENDING) -> None:
        self._state = initial

    @property
    def state(self) -> WorkflowState:
        return self._state

    def transition(self, target: WorkflowState) -> WorkflowState:
        if target not in _WORKFLOW_TRANSITIONS.get(self._state, set()):
            msg = f"invalid transition from {self._state} to {target}"
            raise InvalidStateTransitionError(msg)
        self._state = target
        return self._state

    def can_transition(self, target: WorkflowState) -> bool:
        return target in _WORKFLOW_TRANSITIONS.get(self._state, set())

    def is_terminal(self) -> bool:
        return not _WORKFLOW_TRANSITIONS.get(self._state, set())

    def is_active(self) -> bool:
        return self._state in {
            WorkflowState.PENDING,
            WorkflowState.RUNNING,
            WorkflowState.PAUSED,
            WorkflowState.WAITING_APPROVAL,
        }

    def reset(self) -> None:
        self._state = WorkflowState.PENDING


class StepStateMachine:
    """Finite state machine for workflow step lifecycle."""

    def __init__(self, initial: StepState = StepState.PENDING) -> None:
        self._state = initial

    @property
    def state(self) -> StepState:
        return self._state

    def transition(self, target: StepState) -> StepState:
        if target not in _STEP_TRANSITIONS.get(self._state, set()):
            msg = f"invalid step transition from {self._state} to {target}"
            raise InvalidStateTransitionError(msg)
        self._state = target
        return self._state

    def can_transition(self, target: StepState) -> bool:
        return target in _STEP_TRANSITIONS.get(self._state, set())

    def is_terminal(self) -> bool:
        return not _STEP_TRANSITIONS.get(self._state, set())

    def is_active(self) -> bool:
        return self._state in {
            StepState.PENDING,
            StepState.RUNNING,
            StepState.WAITING_APPROVAL,
        }

    def reset(self) -> None:
        self._state = StepState.PENDING


class InvalidStateTransitionError(ValueError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


__all__ = [
    "InvalidStateTransitionError",
    "StepState",
    "StepStateMachine",
    "WorkflowState",
    "WorkflowStateMachine",
]
