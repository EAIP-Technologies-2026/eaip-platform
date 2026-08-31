"""Tests for PublishingWorkflowEngine."""

from __future__ import annotations

import pytest

from eaip.content.exceptions import WorkflowNotFoundError
from eaip.content.models import (
    WorkflowStatus,
    WorkflowStep,
    WorkflowStepStatus,
    WorkflowStepType,
)
from eaip.content.workflow import PublishingWorkflowEngine


class TestPublishingWorkflowEngine:
    def setup_method(self) -> None:
        self.engine = PublishingWorkflowEngine()

    def test_create_workflow(self) -> None:
        steps = (
            WorkflowStep(id="s1", name="Review", type=WorkflowStepType.REVIEW),
            WorkflowStep(id="s2", name="Approve", type=WorkflowStepType.APPROVAL),
            WorkflowStep(id="s3", name="Publish", type=WorkflowStepType.PUBLISH),
        )
        wf = self.engine.create_workflow(
            workflow_id="wf_1",
            name="Publish Doc",
            steps=steps,
        )
        assert wf.id == "wf_1"
        assert wf.name == "Publish Doc"
        assert len(wf.steps) == 3
        assert wf.status is WorkflowStatus.PENDING

    def test_get_workflow(self) -> None:
        self.engine.create_workflow("wf_1", "Test")
        wf = self.engine.get_workflow("wf_1")
        assert wf.id == "wf_1"

    def test_get_workflow_not_found(self) -> None:
        with pytest.raises(WorkflowNotFoundError) as exc:
            self.engine.get_workflow("missing")
        assert "missing" in str(exc.value)

    async def test_execute_step(self) -> None:
        steps = (WorkflowStep(id="s1", name="Review", type=WorkflowStepType.REVIEW),)
        self.engine.create_workflow("wf_1", "Test", steps=steps)
        result = await self.engine.execute_step("wf_1", "s1")
        assert result.status is WorkflowStatus.RUNNING
        step = result.steps[0]
        assert step.status is WorkflowStepStatus.COMPLETED

    def test_advance_workflow(self) -> None:
        steps = (
            WorkflowStep(
                id="s1",
                name="Review",
                type=WorkflowStepType.REVIEW,
                status=WorkflowStepStatus.COMPLETED,
            ),
        )
        self.engine.create_workflow("wf_1", "Test", steps=steps)
        result = self.engine.advance_workflow("wf_1")
        assert result.status is WorkflowStatus.COMPLETED

    def test_advance_workflow_partial(self) -> None:
        steps = (
            WorkflowStep(id="s1", name="Review", type=WorkflowStepType.REVIEW),
            WorkflowStep(id="s2", name="Approve", type=WorkflowStepType.APPROVAL),
        )
        self.engine.create_workflow("wf_1", "Test", steps=steps)
        result = self.engine.advance_workflow("wf_1")
        assert result.status is WorkflowStatus.PENDING

    def test_cancel_workflow(self) -> None:
        steps = (
            WorkflowStep(id="s1", name="Review", type=WorkflowStepType.REVIEW),
            WorkflowStep(id="s2", name="Approve", type=WorkflowStepType.APPROVAL),
        )
        self.engine.create_workflow("wf_1", "Test", steps=steps)
        cancelled = self.engine.cancel_workflow("wf_1")
        assert cancelled.status is WorkflowStatus.CANCELLED
        for step in cancelled.steps:
            assert step.status is WorkflowStepStatus.SKIPPED

    def test_get_workflow_status(self) -> None:
        self.engine.create_workflow("wf_1", "Test")
        assert self.engine.get_workflow_status("wf_1") is WorkflowStatus.PENDING
        self.engine.cancel_workflow("wf_1")
        assert self.engine.get_workflow_status("wf_1") is WorkflowStatus.CANCELLED

    def test_execute_step_not_found(self) -> None:
        self.engine.create_workflow("wf_1", "Test")
        with pytest.raises(ValueError, match="step.*not found"):
            # execute_step calls the engine internally; exception comes from _find_step
            import asyncio

            asyncio.run(self.engine.execute_step("wf_1", "missing_step"))
