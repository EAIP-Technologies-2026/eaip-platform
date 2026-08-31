"""Core service for long-running workflow lifecycle - schedule, execute, checkpoint, recover."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from eaip.long_running.events import (
    WorkflowCheckpointCreated,
    WorkflowExecutionCompleted,
    WorkflowExecutionFailed,
    WorkflowExecutionStarted,
    WorkflowScheduled,
    WorkflowStateRecovered,
)
from eaip.long_running.exceptions import (
    WorkflowCheckpointError,
    WorkflowExecutionTimeoutError,
    WorkflowNotFoundError,
    WorkflowRecoveryError,
)
from eaip.long_running.models import (
    LongRunningWorkflow,
    WorkflowCheckpoint,
    WorkflowExecutionPlan,
    WorkflowPersistenceConfig,
    WorkflowRecoveryStrategy,
    WorkflowSnapshot,
    WorkflowState,
    WorkflowStatus,
)
from eaip.shared.time import utc_now


class LongRunningService:
    def __init__(
        self,
        persistence_config: WorkflowPersistenceConfig | None = None,
    ) -> None:
        self._persistence_config = persistence_config or WorkflowPersistenceConfig()
        self._workflows: dict[str, LongRunningWorkflow] = {}
        self._checkpoints: dict[str, WorkflowCheckpoint] = {}

    @property
    def workflows(self) -> dict[str, LongRunningWorkflow]:
        return dict(self._workflows)

    @property
    def checkpoints(self) -> dict[str, WorkflowCheckpoint]:
        return dict(self._checkpoints)

    async def schedule(
        self,
        workflow_id: str,
        name: str,
        plan: WorkflowExecutionPlan | None = None,
    ) -> WorkflowScheduled:
        state = WorkflowState(
            workflow_id=workflow_id,
            status=WorkflowStatus.PENDING,
        )
        execution_plan = plan or WorkflowExecutionPlan(workflow_id=workflow_id)
        workflow = LongRunningWorkflow(
            id=workflow_id,
            name=name,
            state=state,
            plan=execution_plan,
        )
        self._workflows[workflow_id] = workflow
        return WorkflowScheduled(
            workflow_id=workflow_id,
            workflow_name=name,
            plan=execution_plan,
            scheduled_at=utc_now(),
        )

    async def execute(
        self,
        workflow_id: str,
        step_id: str = "",
        context: dict[str, Any] | None = None,
    ) -> WorkflowExecutionStarted:
        workflow = self._workflows.get(workflow_id)
        if workflow is None:
            raise WorkflowNotFoundError(workflow_id)

        plan = workflow.plan
        if plan.execution_timeout_seconds > 0:
            elapsed = (utc_now() - workflow.state.started_at).total_seconds()
            if elapsed > plan.execution_timeout_seconds:
                raise WorkflowExecutionTimeoutError(workflow_id, plan.execution_timeout_seconds)

        new_state = WorkflowState(
            workflow_id=workflow_id,
            status=WorkflowStatus.RUNNING,
            context=context or workflow.state.context,
            step_id=step_id or workflow.state.step_id,
            attempt=workflow.state.attempt + 1,
            started_at=workflow.state.started_at,
            updated_at=utc_now(),
        )
        updated = LongRunningWorkflow(
            id=workflow.id,
            name=workflow.name,
            description=workflow.description,
            version=workflow.version,
            state=new_state,
            plan=plan,
            checkpoints=workflow.checkpoints,
            continuation_token=workflow.continuation_token,
            tags=workflow.tags,
            metadata=workflow.metadata,
        )
        self._workflows[workflow_id] = updated
        return WorkflowExecutionStarted(
            workflow_id=workflow_id,
            workflow_name=workflow.name,
            state=new_state,
            step_id=step_id,
        )

    async def checkpoint(
        self,
        workflow_id: str,
        checkpoint_id: str,
        step_id: str = "",
        snapshot_context: dict[str, Any] | None = None,
        variables: dict[str, Any] | None = None,
    ) -> WorkflowCheckpointCreated:
        workflow = self._workflows.get(workflow_id)
        if workflow is None:
            raise WorkflowNotFoundError(workflow_id)

        if len(self._checkpoints) >= workflow.plan.persistence.max_checkpoints:
            raise WorkflowCheckpointError(
                workflow_id,
                f"max checkpoints ({workflow.plan.persistence.max_checkpoints}) reached",
            )

        state = WorkflowState(
            workflow_id=workflow_id,
            status=WorkflowStatus.CHECKPOINTED,
            context=workflow.state.context,
            step_id=step_id or workflow.state.step_id,
            attempt=workflow.state.attempt,
            started_at=workflow.state.started_at,
            updated_at=utc_now(),
        )
        snapshot = WorkflowSnapshot(
            state=state,
            context=snapshot_context or workflow.state.context,
            variables=variables or {},
            captured_at=utc_now(),
        )
        ttl = workflow.plan.persistence.checkpoint_ttl_seconds
        expires = None
        if ttl > 0:
            expires = datetime.fromtimestamp(utc_now().timestamp() + ttl)

        checkpoint = WorkflowCheckpoint(
            id=checkpoint_id,
            workflow_id=workflow_id,
            step_id=step_id,
            snapshot=snapshot,
            created_at=utc_now(),
            expires_at=expires,
        )
        self._checkpoints[checkpoint_id] = checkpoint

        updated_state = WorkflowState(
            workflow_id=workflow_id,
            status=WorkflowStatus.CHECKPOINTED,
            context=workflow.state.context,
            step_id=step_id or workflow.state.step_id,
            attempt=workflow.state.attempt,
            started_at=workflow.state.started_at,
            updated_at=utc_now(),
        )
        old_checkpoints = workflow.checkpoints
        updated = LongRunningWorkflow(
            id=workflow.id,
            name=workflow.name,
            description=workflow.description,
            version=workflow.version,
            state=updated_state,
            plan=workflow.plan,
            checkpoints=(*old_checkpoints, checkpoint),
            continuation_token=workflow.continuation_token,
            tags=workflow.tags,
            metadata=workflow.metadata,
        )
        self._workflows[workflow_id] = updated
        return WorkflowCheckpointCreated(
            workflow_id=workflow_id,
            checkpoint=checkpoint,
        )

    async def recover(
        self,
        workflow_id: str,
        strategy: WorkflowRecoveryStrategy | None = None,
    ) -> WorkflowStateRecovered:
        workflow = self._workflows.get(workflow_id)
        if workflow is None:
            raise WorkflowNotFoundError(workflow_id)

        recover_strategy = strategy or workflow.plan.recovery_strategy
        if recover_strategy == WorkflowRecoveryStrategy.RESTART:
            new_state = WorkflowState(
                workflow_id=workflow_id,
                status=WorkflowStatus.RUNNING,
                attempt=workflow.state.attempt + 1,
                started_at=utc_now(),
                updated_at=utc_now(),
            )
            recovered_step_id = ""
        elif recover_strategy == WorkflowRecoveryStrategy.RESUME:
            checkpoints = workflow.checkpoints
            if not checkpoints:
                raise WorkflowRecoveryError(workflow_id, "no checkpoints available to resume from")
            latest = checkpoints[-1]
            new_state = WorkflowState(
                workflow_id=workflow_id,
                status=WorkflowStatus.RUNNING,
                context=latest.snapshot.context,
                step_id=latest.snapshot.state.step_id,
                attempt=workflow.state.attempt + 1,
                started_at=utc_now(),
                updated_at=utc_now(),
            )
            recovered_step_id = latest.snapshot.state.step_id
        elif recover_strategy == WorkflowRecoveryStrategy.SKIP_COMPLETED:
            new_state = WorkflowState(
                workflow_id=workflow_id,
                status=WorkflowStatus.RUNNING,
                context=workflow.state.context,
                step_id=workflow.state.step_id,
                attempt=workflow.state.attempt + 1,
                started_at=utc_now(),
                updated_at=utc_now(),
            )
            recovered_step_id = workflow.state.step_id
        else:
            new_state = WorkflowState(
                workflow_id=workflow_id,
                status=WorkflowStatus.RUNNING,
                attempt=workflow.state.attempt + 1,
                started_at=utc_now(),
                updated_at=utc_now(),
            )
            recovered_step_id = ""

        updated = LongRunningWorkflow(
            id=workflow.id,
            name=workflow.name,
            description=workflow.description,
            version=workflow.version,
            state=new_state,
            plan=workflow.plan,
            checkpoints=workflow.checkpoints,
            continuation_token=workflow.continuation_token,
            tags=workflow.tags,
            metadata=workflow.metadata,
        )
        self._workflows[workflow_id] = updated
        return WorkflowStateRecovered(
            workflow_id=workflow_id,
            strategy=recover_strategy,
            recovered_step_id=recovered_step_id,
        )

    async def complete(
        self,
        workflow_id: str,
        result: str = "",
    ) -> WorkflowExecutionCompleted:
        workflow = self._workflows.get(workflow_id)
        if workflow is None:
            raise WorkflowNotFoundError(workflow_id)

        now = utc_now()
        duration = (now - workflow.state.started_at).total_seconds() * 1000
        new_state = WorkflowState(
            workflow_id=workflow_id,
            status=WorkflowStatus.COMPLETED,
            context=workflow.state.context,
            step_id=workflow.state.step_id,
            attempt=workflow.state.attempt,
            started_at=workflow.state.started_at,
            updated_at=now,
            completed_at=now,
        )
        updated = LongRunningWorkflow(
            id=workflow.id,
            name=workflow.name,
            description=workflow.description,
            version=workflow.version,
            state=new_state,
            plan=workflow.plan,
            checkpoints=workflow.checkpoints,
            continuation_token=workflow.continuation_token,
            tags=workflow.tags,
            metadata=workflow.metadata,
        )
        self._workflows[workflow_id] = updated
        return WorkflowExecutionCompleted(
            workflow_id=workflow_id,
            workflow_name=workflow.name,
            status=WorkflowStatus.COMPLETED,
            duration_ms=duration,
            result=result,
        )

    async def fail(
        self,
        workflow_id: str,
        error: str = "",
        will_retry: bool = False,
    ) -> WorkflowExecutionFailed:
        workflow = self._workflows.get(workflow_id)
        if workflow is None:
            raise WorkflowNotFoundError(workflow_id)

        new_state = WorkflowState(
            workflow_id=workflow_id,
            status=WorkflowStatus.FAILED,
            context=workflow.state.context,
            step_id=workflow.state.step_id,
            attempt=workflow.state.attempt,
            started_at=workflow.state.started_at,
            updated_at=utc_now(),
            completed_at=utc_now(),
            error=error,
        )
        updated = LongRunningWorkflow(
            id=workflow.id,
            name=workflow.name,
            description=workflow.description,
            version=workflow.version,
            state=new_state,
            plan=workflow.plan,
            checkpoints=workflow.checkpoints,
            continuation_token=workflow.continuation_token,
            tags=workflow.tags,
            metadata=workflow.metadata,
        )
        self._workflows[workflow_id] = updated
        return WorkflowExecutionFailed(
            workflow_id=workflow_id,
            workflow_name=workflow.name,
            error=error,
            step_id=workflow.state.step_id,
            attempt=workflow.state.attempt,
            will_retry=will_retry,
        )

    async def get_workflow(self, workflow_id: str) -> LongRunningWorkflow:
        workflow = self._workflows.get(workflow_id)
        if workflow is None:
            raise WorkflowNotFoundError(workflow_id)
        return workflow


__all__ = ["LongRunningService"]
