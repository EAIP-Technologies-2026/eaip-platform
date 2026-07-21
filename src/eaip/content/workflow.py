"""PublishingWorkflowEngine - manages publishing workflows with step execution and timeouts."""

from __future__ import annotations

import asyncio

from eaip.content.exceptions import WorkflowNotFoundError
from eaip.content.models import (
    PublishingWorkflow,
    WorkflowStatus,
    WorkflowStep,
    WorkflowStepStatus,
)


class PublishingWorkflowEngine:
    """Engine for executing publishing workflow steps sequentially."""

    def __init__(self) -> None:
        self._workflows: dict[str, PublishingWorkflow] = {}

    def create_workflow(
        self,
        workflow_id: str,
        name: str,
        steps: tuple[WorkflowStep, ...] = (),
    ) -> PublishingWorkflow:
        workflow = PublishingWorkflow(
            id=workflow_id,
            name=name,
            steps=steps,
            status=WorkflowStatus.PENDING,
        )
        self._workflows[workflow_id] = workflow
        return workflow

    def get_workflow(self, workflow_id: str) -> PublishingWorkflow:
        workflow = self._workflows.get(workflow_id)
        if workflow is None:
            raise WorkflowNotFoundError(workflow_id)
        return workflow

    async def execute_step(self, workflow_id: str, step_id: str) -> PublishingWorkflow:
        workflow = self.get_workflow(workflow_id)
        step = self._find_step(workflow, step_id)

        timeout = step.timeout_hours * 3600 if step.timeout_hours > 0 else None
        updated_steps: list[WorkflowStep] = []
        for s in workflow.steps:
            if s.id == step_id:
                updated_steps.append(
                    WorkflowStep(
                        id=s.id,
                        name=s.name,
                        type=s.type,
                        assignees=s.assignees,
                        status=WorkflowStepStatus.RUNNING,
                        timeout_hours=s.timeout_hours,
                        metadata=s.metadata,
                    )
                )
            else:
                updated_steps.append(s)

        workflow = PublishingWorkflow(
            id=workflow.id,
            name=workflow.name,
            steps=tuple(updated_steps),
            status=WorkflowStatus.RUNNING,
            created_at=workflow.created_at,
        )
        self._workflows[workflow_id] = workflow

        try:
            if timeout is not None:
                await asyncio.sleep(0)
            completed_steps: list[WorkflowStep] = []
            for s in updated_steps:
                if s.id == step_id:
                    completed_steps.append(
                        WorkflowStep(
                            id=s.id,
                            name=s.name,
                            type=s.type,
                            assignees=s.assignees,
                            status=WorkflowStepStatus.COMPLETED,
                            timeout_hours=s.timeout_hours,
                            metadata=s.metadata,
                        )
                    )
                else:
                    completed_steps.append(s)
            workflow = PublishingWorkflow(
                id=workflow.id,
                name=workflow.name,
                steps=tuple(completed_steps),
                status=WorkflowStatus.RUNNING,
                created_at=workflow.created_at,
            )
            self._workflows[workflow_id] = workflow
            return workflow
        except TimeoutError:
            failed_steps: list[WorkflowStep] = []
            for s in updated_steps:
                if s.id == step_id:
                    failed_steps.append(
                        WorkflowStep(
                            id=s.id,
                            name=s.name,
                            type=s.type,
                            assignees=s.assignees,
                            status=WorkflowStepStatus.TIMED_OUT,
                            timeout_hours=s.timeout_hours,
                            metadata=s.metadata,
                        )
                    )
                else:
                    failed_steps.append(s)
            workflow = PublishingWorkflow(
                id=workflow.id,
                name=workflow.name,
                steps=tuple(failed_steps),
                status=WorkflowStatus.FAILED,
                created_at=workflow.created_at,
            )
            self._workflows[workflow_id] = workflow
            return workflow

    def advance_workflow(self, workflow_id: str) -> PublishingWorkflow:
        workflow = self.get_workflow(workflow_id)
        all_completed = all(s.status == WorkflowStepStatus.COMPLETED for s in workflow.steps)
        if all_completed:
            workflow = PublishingWorkflow(
                id=workflow.id,
                name=workflow.name,
                steps=workflow.steps,
                status=WorkflowStatus.COMPLETED,
                created_at=workflow.created_at,
            )
            self._workflows[workflow_id] = workflow
        return workflow

    def cancel_workflow(self, workflow_id: str) -> PublishingWorkflow:
        workflow = self.get_workflow(workflow_id)
        cancelled_steps: list[WorkflowStep] = []
        for s in workflow.steps:
            if s.status in (WorkflowStepStatus.PENDING, WorkflowStepStatus.RUNNING):
                cancelled_steps.append(
                    WorkflowStep(
                        id=s.id,
                        name=s.name,
                        type=s.type,
                        assignees=s.assignees,
                        status=WorkflowStepStatus.SKIPPED,
                        timeout_hours=s.timeout_hours,
                        metadata=s.metadata,
                    )
                )
            else:
                cancelled_steps.append(s)
        workflow = PublishingWorkflow(
            id=workflow.id,
            name=workflow.name,
            steps=tuple(cancelled_steps),
            status=WorkflowStatus.CANCELLED,
            created_at=workflow.created_at,
        )
        self._workflows[workflow_id] = workflow
        return workflow

    def get_workflow_status(self, workflow_id: str) -> WorkflowStatus:
        return self.get_workflow(workflow_id).status

    def _find_step(self, workflow: PublishingWorkflow, step_id: str) -> WorkflowStep:
        for step in workflow.steps:
            if step.id == step_id:
                return step
        raise ValueError(f"step {step_id!r} not found in workflow {workflow.id!r}")


__all__ = [
    "PublishingWorkflowEngine",
]
