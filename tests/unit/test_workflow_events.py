"""Tests for Workflow domain event models."""

from __future__ import annotations

from eaip.events.event import DomainEvent
from eaip.workflow.events import (
    WorkflowChildCompleted,
    WorkflowChildStarted,
    WorkflowCompleted,
    WorkflowParallelGroupCompleted,
    WorkflowParallelGroupStarted,
    WorkflowPaused,
    WorkflowResumed,
    WorkflowStarted,
    WorkflowStepApprovalRequired,
    WorkflowStepApproved,
    WorkflowStepCompleted,
    WorkflowStepFailed,
    WorkflowStepRejected,
    WorkflowStepSkipped,
    WorkflowStepStarted,
    WorkflowStepTimedOut,
    WorkflowTimedOut,
)
from eaip.workflow.models import WorkflowStatus


class TestWorkflowStarted:
    def test_defaults(self) -> None:
        e = WorkflowStarted()
        assert e.event_type == "eaip.workflow.started"
        assert isinstance(e, DomainEvent)
        assert e.run_id == ""
        assert e.definition_name == ""

    def test_with_values(self) -> None:
        e = WorkflowStarted(run_id="r1", workflow_id="wf_1", definition_name="Test")
        assert e.run_id == "r1"
        assert e.workflow_id == "wf_1"
        assert e.definition_name == "Test"

    def test_frozen(self) -> None:
        e = WorkflowStarted(run_id="r1")
        try:
            e.run_id = "r2"
            raise AssertionError("should be frozen")
        except (ValueError, TypeError):
            pass


class TestWorkflowStepStarted:
    def test_defaults(self) -> None:
        e = WorkflowStepStarted()
        assert e.event_type == "eaip.workflow.step.started"
        assert e.attempt == 0

    def test_with_values(self) -> None:
        e = WorkflowStepStarted(run_id="r1", step_id="s1", step_name="Analyze", attempt=1)
        assert e.step_name == "Analyze"
        assert e.attempt == 1


class TestWorkflowStepCompleted:
    def test_defaults(self) -> None:
        e = WorkflowStepCompleted()
        assert e.event_type == "eaip.workflow.step.completed"
        assert e.duration_ms == 0.0

    def test_with_values(self) -> None:
        e = WorkflowStepCompleted(run_id="r1", step_id="s1", duration_ms=150.0)
        assert e.duration_ms == 150.0


class TestWorkflowStepFailed:
    def test_defaults(self) -> None:
        e = WorkflowStepFailed()
        assert e.event_type == "eaip.workflow.step.failed"
        assert not e.will_retry

    def test_with_values(self) -> None:
        e = WorkflowStepFailed(run_id="r1", step_id="s1", error="timeout", will_retry=True)
        assert e.error == "timeout"
        assert e.will_retry


class TestWorkflowStepApprovalRequired:
    def test_defaults(self) -> None:
        e = WorkflowStepApprovalRequired()
        assert e.event_type == "eaip.workflow.step.approval_required"
        assert e.payload is None

    def test_with_payload(self) -> None:
        e = WorkflowStepApprovalRequired(
            run_id="r1", step_id="s1", payload={"reason": "review"}, resume_token="tok_1",
        )
        assert e.payload == {"reason": "review"}
        assert e.resume_token == "tok_1"


class TestWorkflowStepApproved:
    def test_defaults(self) -> None:
        e = WorkflowStepApproved()
        assert e.event_type == "eaip.workflow.step.approved"

    def test_with_values(self) -> None:
        e = WorkflowStepApproved(run_id="r1", step_id="s1", resume_token="tok_1")
        assert e.resume_token == "tok_1"


class TestWorkflowStepRejected:
    def test_defaults(self) -> None:
        e = WorkflowStepRejected()
        assert e.event_type == "eaip.workflow.step.rejected"

    def test_with_reason(self) -> None:
        e = WorkflowStepRejected(run_id="r1", step_id="s1", reason="bad data")
        assert e.reason == "bad data"


class TestWorkflowStepSkipped:
    def test_defaults(self) -> None:
        e = WorkflowStepSkipped()
        assert e.event_type == "eaip.workflow.step.skipped"

    def test_with_values(self) -> None:
        e = WorkflowStepSkipped(run_id="r1", step_id="s1", step_name="Optional")
        assert e.step_name == "Optional"


class TestWorkflowCompleted:
    def test_defaults(self) -> None:
        e = WorkflowCompleted()
        assert e.event_type == "eaip.workflow.completed"
        assert e.status is WorkflowStatus.COMPLETED

    def test_failed(self) -> None:
        e = WorkflowCompleted(
            run_id="r1",
            workflow_id="wf_1",
            status=WorkflowStatus.FAILED,
            error="oops",
            failed_count=1,
        )
        assert e.status is WorkflowStatus.FAILED
        assert e.error == "oops"
        assert e.failed_count == 1

    def test_frozen(self) -> None:
        e = WorkflowCompleted()
        try:
            e.status = WorkflowStatus.FAILED
            raise AssertionError("should be frozen")
        except (ValueError, TypeError):
            pass


class TestWorkflowStepTimedOut:
    def test_defaults(self) -> None:
        e = WorkflowStepTimedOut()
        assert e.event_type == "eaip.workflow.step.timed_out"
        assert e.timeout_seconds == 0.0

    def test_with_values(self) -> None:
        e = WorkflowStepTimedOut(run_id="r1", step_id="s1", timeout_seconds=30.0)
        assert e.timeout_seconds == 30.0


class TestWorkflowTimedOut:
    def test_defaults(self) -> None:
        e = WorkflowTimedOut()
        assert e.event_type == "eaip.workflow.timed_out"

    def test_with_values(self) -> None:
        e = WorkflowTimedOut(run_id="r1", workflow_id="wf_1", timeout_seconds=60.0)
        assert e.timeout_seconds == 60.0


class TestWorkflowPaused:
    def test_defaults(self) -> None:
        e = WorkflowPaused()
        assert e.event_type == "eaip.workflow.paused"


class TestWorkflowResumed:
    def test_defaults(self) -> None:
        e = WorkflowResumed()
        assert e.event_type == "eaip.workflow.resumed"


class TestWorkflowChildStarted:
    def test_defaults(self) -> None:
        e = WorkflowChildStarted()
        assert e.event_type == "eaip.workflow.child.started"

    def test_with_values(self) -> None:
        e = WorkflowChildStarted(parent_run_id="p1", child_run_id="c1", workflow_id="wf_1")
        assert e.parent_run_id == "p1"
        assert e.child_run_id == "c1"


class TestWorkflowChildCompleted:
    def test_defaults(self) -> None:
        e = WorkflowChildCompleted()
        assert e.event_type == "eaip.workflow.child.completed"

    def test_with_values(self) -> None:
        e = WorkflowChildCompleted(parent_run_id="p1", child_run_id="c1", duration_ms=500.0)
        assert e.duration_ms == 500.0


class TestWorkflowParallelGroupStarted:
    def test_defaults(self) -> None:
        e = WorkflowParallelGroupStarted()
        assert e.event_type == "eaip.workflow.parallel.started"

    def test_with_values(self) -> None:
        e = WorkflowParallelGroupStarted(run_id="r1", group_id="g1", step_count=3)
        assert e.group_id == "g1"
        assert e.step_count == 3


class TestWorkflowParallelGroupCompleted:
    def test_defaults(self) -> None:
        e = WorkflowParallelGroupCompleted()
        assert e.event_type == "eaip.workflow.parallel.completed"

    def test_with_values(self) -> None:
        e = WorkflowParallelGroupCompleted(run_id="r1", group_id="g1", completed=2, failed=0)
        assert e.completed == 2
        assert e.failed == 0
