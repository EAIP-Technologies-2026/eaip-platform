"""Tests for Workflow State Machine."""

from __future__ import annotations

import pytest

from eaip.workflow.state_machine import (
    InvalidStateTransitionError,
    StepState,
    StepStateMachine,
    WorkflowState,
    WorkflowStateMachine,
)


class TestWorkflowStateMachine:
    def test_initial_state(self) -> None:
        sm = WorkflowStateMachine()
        assert sm.state is WorkflowState.PENDING

    def test_initial_custom(self) -> None:
        sm = WorkflowStateMachine(WorkflowState.RUNNING)
        assert sm.state is WorkflowState.RUNNING

    def test_valid_transition(self) -> None:
        sm = WorkflowStateMachine()
        sm.transition(WorkflowState.RUNNING)
        assert sm.state is WorkflowState.RUNNING

    def test_invalid_transition(self) -> None:
        sm = WorkflowStateMachine()
        with pytest.raises(InvalidStateTransitionError, match="invalid transition"):
            sm.transition(WorkflowState.COMPLETED)

    def test_full_lifecycle(self) -> None:
        sm = WorkflowStateMachine()
        sm.transition(WorkflowState.RUNNING)
        sm.transition(WorkflowState.COMPLETED)
        assert sm.state is WorkflowState.COMPLETED

    def test_pause_resume(self) -> None:
        sm = WorkflowStateMachine()
        sm.transition(WorkflowState.RUNNING)
        sm.transition(WorkflowState.PAUSED)
        assert sm.state is WorkflowState.PAUSED
        sm.transition(WorkflowState.RUNNING)
        assert sm.state is WorkflowState.RUNNING

    def test_waiting_approval(self) -> None:
        sm = WorkflowStateMachine()
        sm.transition(WorkflowState.RUNNING)
        sm.transition(WorkflowState.WAITING_APPROVAL)
        assert sm.state is WorkflowState.WAITING_APPROVAL

    def test_can_transition(self) -> None:
        sm = WorkflowStateMachine()
        assert sm.can_transition(WorkflowState.RUNNING)
        assert sm.can_transition(WorkflowState.CANCELLED)
        assert not sm.can_transition(WorkflowState.COMPLETED)

    def test_is_terminal(self) -> None:
        sm = WorkflowStateMachine()
        assert not sm.is_terminal()
        sm.transition(WorkflowState.RUNNING)
        sm.transition(WorkflowState.COMPLETED)
        assert sm.is_terminal()

    def test_is_terminal_failed(self) -> None:
        sm = WorkflowStateMachine()
        sm.transition(WorkflowState.RUNNING)
        sm.transition(WorkflowState.FAILED)
        assert sm.is_terminal()

    def test_is_terminal_cancelled(self) -> None:
        sm = WorkflowStateMachine()
        sm.transition(WorkflowState.RUNNING)
        sm.transition(WorkflowState.CANCELLED)
        assert sm.is_terminal()

    def test_is_active(self) -> None:
        sm = WorkflowStateMachine()
        assert sm.is_active()
        sm.transition(WorkflowState.RUNNING)
        assert sm.is_active()
        sm.transition(WorkflowState.COMPLETED)
        assert not sm.is_active()

    def test_reset(self) -> None:
        sm = WorkflowStateMachine()
        sm.transition(WorkflowState.RUNNING)
        sm.transition(WorkflowState.COMPLETED)
        sm.reset()
        assert sm.state is WorkflowState.PENDING
        assert sm.is_active()

    def test_timed_out_transition(self) -> None:
        sm = WorkflowStateMachine()
        sm.transition(WorkflowState.RUNNING)
        sm.transition(WorkflowState.TIMED_OUT)
        assert sm.state is WorkflowState.TIMED_OUT
        assert sm.is_terminal()

    def test_timed_out_invalid_from_pending(self) -> None:
        sm = WorkflowStateMachine()
        with pytest.raises(InvalidStateTransitionError):
            sm.transition(WorkflowState.TIMED_OUT)


class TestStepStateMachine:
    def test_initial_state(self) -> None:
        sm = StepStateMachine()
        assert sm.state is StepState.PENDING

    def test_valid_transition(self) -> None:
        sm = StepStateMachine()
        sm.transition(StepState.RUNNING)
        sm.transition(StepState.COMPLETED)
        assert sm.state is StepState.COMPLETED

    def test_invalid_transition(self) -> None:
        sm = StepStateMachine()
        with pytest.raises(InvalidStateTransitionError):
            sm.transition(StepState.COMPLETED)

    def test_approval_flow(self) -> None:
        sm = StepStateMachine()
        sm.transition(StepState.RUNNING)
        sm.transition(StepState.WAITING_APPROVAL)
        assert sm.state is StepState.WAITING_APPROVAL
        sm.transition(StepState.APPROVED)
        assert sm.state is StepState.APPROVED
        sm.transition(StepState.RUNNING)
        assert sm.state is StepState.RUNNING

    def test_rejected(self) -> None:
        sm = StepStateMachine()
        sm.transition(StepState.RUNNING)
        sm.transition(StepState.WAITING_APPROVAL)
        sm.transition(StepState.REJECTED)
        assert sm.state is StepState.REJECTED
        assert not sm.is_terminal()
        sm.transition(StepState.FAILED)
        assert sm.state is StepState.FAILED
        assert sm.is_terminal()

    def test_skip(self) -> None:
        sm = StepStateMachine()
        sm.transition(StepState.SKIPPED)
        assert sm.is_terminal()

    def test_blocked_unblock(self) -> None:
        sm = StepStateMachine()
        sm.transition(StepState.BLOCKED)
        assert not sm.is_terminal()
        sm.transition(StepState.PENDING)
        assert sm.state is StepState.PENDING

    def test_timed_out(self) -> None:
        sm = StepStateMachine()
        sm.transition(StepState.RUNNING)
        sm.transition(StepState.TIMED_OUT)
        assert sm.is_terminal()

    def test_can_transition(self) -> None:
        sm = StepStateMachine()
        assert sm.can_transition(StepState.RUNNING)
        assert sm.can_transition(StepState.SKIPPED)
        assert not sm.can_transition(StepState.COMPLETED)
        assert not sm.can_transition(StepState.FAILED)

    def test_is_active(self) -> None:
        sm = StepStateMachine()
        assert sm.is_active()
        sm.transition(StepState.RUNNING)
        assert sm.is_active()
        sm.transition(StepState.COMPLETED)
        assert not sm.is_active()

    def test_reset(self) -> None:
        sm = StepStateMachine()
        sm.transition(StepState.RUNNING)
        sm.transition(StepState.COMPLETED)
        sm.reset()
        assert sm.state is StepState.PENDING
