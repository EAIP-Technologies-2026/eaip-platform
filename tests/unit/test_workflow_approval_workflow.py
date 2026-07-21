from __future__ import annotations

import pytest

from eaip.workflow.approval_workflow import ApprovalStep, ApprovalStepStatus, ApprovalWorkflow


class TestApprovalWorkflow:
    def test_create_workflow(self) -> None:
        step1 = ApprovalStep(step_id="s1", workflow_id="wf1", order=1, approver="alice")
        wf = ApprovalWorkflow(workflow_id="wf1", name="test", initiator="bob", steps=[step1])
        assert wf.workflow_id == "wf1"
        assert len(wf.get_steps()) == 1

    def test_approve_step(self) -> None:
        step1 = ApprovalStep(step_id="s1", workflow_id="wf1", order=1, approver="alice")
        wf = ApprovalWorkflow(workflow_id="wf1", name="test", initiator="bob", steps=[step1])
        result = wf.approve("s1", "looks good")
        assert result is True
        assert wf.is_completed is True
        assert wf.is_approved is True

    def test_reject_step(self) -> None:
        step1 = ApprovalStep(step_id="s1", workflow_id="wf1", order=1, approver="alice")
        wf = ApprovalWorkflow(workflow_id="wf1", name="test", initiator="bob", steps=[step1])
        result = wf.reject("s1", "not approved")
        assert result is True
        assert wf.is_completed is True
        assert wf.is_approved is False

    def test_approve_out_of_order(self) -> None:
        step1 = ApprovalStep(step_id="s1", workflow_id="wf1", order=1, approver="alice")
        step2 = ApprovalStep(step_id="s2", workflow_id="wf1", order=2, approver="charlie")
        wf = ApprovalWorkflow(workflow_id="wf1", name="test", initiator="bob", steps=[step1, step2])
        result = wf.approve("s2")
        assert result is False

    def test_get_pending_step(self) -> None:
        step1 = ApprovalStep(step_id="s1", workflow_id="wf1", order=1, approver="alice")
        step2 = ApprovalStep(step_id="s2", workflow_id="wf1", order=2, approver="charlie")
        wf = ApprovalWorkflow(workflow_id="wf1", name="test", initiator="bob", steps=[step1, step2])
        pending = wf.get_pending_step()
        assert pending is not None
        assert pending.step_id == "s1"

    def test_multi_step_approval(self) -> None:
        step1 = ApprovalStep(step_id="s1", workflow_id="wf1", order=1, approver="alice")
        step2 = ApprovalStep(step_id="s2", workflow_id="wf1", order=2, approver="charlie")
        wf = ApprovalWorkflow(workflow_id="wf1", name="test", initiator="bob", steps=[step1, step2])
        wf.approve("s1")
        assert wf.is_completed is False
        wf.approve("s2")
        assert wf.is_completed is True

    def test_delegate(self) -> None:
        step1 = ApprovalStep(step_id="s1", workflow_id="wf1", order=1, approver="alice")
        wf = ApprovalWorkflow(workflow_id="wf1", name="test", initiator="bob", steps=[step1])
        result = wf.delegate("s1", "dave")
        assert result is True
        assert step1.delegate_to == "dave"

    def test_check_deadlines(self) -> None:
        step1 = ApprovalStep(
            step_id="s1", workflow_id="wf1", order=1, approver="alice", deadline_minutes=0
        )
        wf = ApprovalWorkflow(workflow_id="wf1", name="test", initiator="bob", steps=[step1])
        escalated = wf.check_deadlines()
        assert len(escalated) == 1
        assert escalated[0].status == ApprovalStepStatus.ESCALATED

    def test_current_step_index(self) -> None:
        step1 = ApprovalStep(step_id="s1", workflow_id="wf1", order=1, approver="alice")
        step2 = ApprovalStep(step_id="s2", workflow_id="wf1", order=2, approver="charlie")
        wf = ApprovalWorkflow(workflow_id="wf1", name="test", initiator="bob", steps=[step1, step2])
        assert wf.current_step_index() == 0
        wf.approve("s1")
        assert wf.current_step_index() == 1
