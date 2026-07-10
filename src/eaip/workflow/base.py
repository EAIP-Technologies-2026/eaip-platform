"""Workflow base protocols — WorkflowExecutor, ApprovalHandler, WorkflowPlugin."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from eaip.workflow.events import WorkflowEvent
from eaip.workflow.models import WorkflowContext, WorkflowDefinition, WorkflowResult


@runtime_checkable
class WorkflowExecutor(Protocol):
    """Protocol for workflow execution engines."""

    async def execute(
        self,
        definition: WorkflowDefinition,
        context: WorkflowContext | None = None,
        parent_run_id: str | None = None,
    ) -> WorkflowResult:
        """Execute a workflow definition and return the result."""
        ...

    async def cancel(self, run_id: str) -> None:
        """Cancel a running workflow by run ID."""
        ...

    async def pause(self, run_id: str) -> None:
        """Pause a running workflow."""
        ...

    async def resume(self, run_id: str) -> WorkflowResult:
        """Resume a paused workflow."""
        ...


@runtime_checkable
class ApprovalHandler(Protocol):
    """Protocol for handling human-in-the-loop approval steps."""

    async def request_approval(
        self,
        step_id: str,
        run_id: str,
        payload: dict[str, Any],
        timeout_seconds: float | None = None,
    ) -> str:
        """Request human approval for a step. Returns resume token."""
        ...

    async def approve(self, token: str, run_id: str) -> None:
        """Approve a pending step using resume token."""
        ...

    async def reject(self, token: str, run_id: str, reason: str) -> None:
        """Reject a pending step with a reason."""
        ...


@runtime_checkable
class WorkflowPlugin(Protocol):
    """Protocol for workflow lifecycle plugins."""

    async def on_step_start(
        self,
        run_id: str,
        step_id: str,
        context: WorkflowContext,
        **data: Any,
    ) -> None:
        """Called before each step executes."""
        ...

    async def on_step_end(
        self,
        run_id: str,
        step_id: str,
        context: WorkflowContext,
        status: str,
        **data: Any,
    ) -> None:
        """Called after each step completes or fails."""
        ...

    async def on_workflow_end(
        self,
        run_id: str,
        result: WorkflowResult,
        **data: Any,
    ) -> None:
        """Called when a workflow finishes (any terminal status)."""
        ...

    async def on_event(
        self,
        event: WorkflowEvent,
        **data: Any,
    ) -> None:
        """Called for every workflow domain event."""
        ...


__all__ = [
    "ApprovalHandler",
    "WorkflowExecutor",
    "WorkflowPlugin",
]
