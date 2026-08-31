"""RuntimeKernel integration - registers WorkflowEngine as a RuntimeModule."""

from __future__ import annotations

from typing import Any

from eaip.events.bus import EventBus
from eaip.events.event import DomainEvent
from eaip.workflow.approval import StepApprovalHandler
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
from eaip.workflow.executor import WorkflowEngine
from eaip.workflow.health import WorkflowHealthCheck


class WorkflowModule:
    """Runtime module that registers WorkflowEngine with the kernel.

    On startup:
      - registers WorkflowEngine as ``workflow.engine``
      - registers WorkflowHealthCheck as ``health.workflow``
      - registers StepApprovalHandler as ``workflow.approval``
      - subscribes to all workflow domain events.

    On shutdown:
      - cancels any active runs.
    """

    name: str = "workflow"

    def __init__(self, engine: WorkflowEngine) -> None:
        self._engine = engine
        self._health_check = WorkflowHealthCheck()
        self._approval_handler = StepApprovalHandler()

    async def start(self, kernel: Any) -> None:
        kernel.services["workflow.engine"] = self._engine
        kernel.services["workflow.health"] = self._health_check
        kernel.services["workflow.approval"] = self._approval_handler

        bus = kernel.services.get("event.bus")
        if isinstance(bus, EventBus):
            self._subscribe_all(bus)

    async def stop(self, _kernel: Any) -> None:
        for rid in list(self._engine._runs or {}):
            await self._engine.cancel(rid)

    def _subscribe_all(self, bus: EventBus) -> None:
        for event_cls in (
            WorkflowStarted,
            WorkflowStepStarted,
            WorkflowStepCompleted,
            WorkflowStepFailed,
            WorkflowStepApprovalRequired,
            WorkflowStepApproved,
            WorkflowStepRejected,
            WorkflowStepSkipped,
            WorkflowStepTimedOut,
            WorkflowTimedOut,
            WorkflowCompleted,
            WorkflowPaused,
            WorkflowResumed,
            WorkflowChildStarted,
            WorkflowChildCompleted,
            WorkflowParallelGroupStarted,
            WorkflowParallelGroupCompleted,
        ):
            bus.subscribe(event_cls, self._handle_event)

    async def _handle_event(self, event: DomainEvent) -> None:
        pass  # Subclasses may override for logging, metrics, etc.


__all__ = [
    "WorkflowModule",
]
