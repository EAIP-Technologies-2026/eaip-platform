"""WorkforceOrchestrator — assigns tasks to workers and manages execution lifecycle."""

from __future__ import annotations

import time
import uuid
from datetime import datetime
from typing import Any, cast

from eaip.logging.context import get_logger
from eaip.workforce.events import (
    WorkerAssigned,
    WorkerAssignmentCompleted,
    WorkerAssignmentFailed,
)
from eaip.workforce.exceptions import (
    AssignmentError,
    WorkerBusyError,
    WorkerNotFoundError,
)
from eaip.workforce.models import (
    AssignmentStatus,
    WorkerAssignment,
    WorkerDefinition,
    WorkerType,
    WorkforceMetrics,
)
from eaip.workforce.worker import WorkerRegistry


class WorkforceOrchestrator:
    """Orchestrates worker assignments and execution lifecycle."""

    def __init__(
        self,
        registry: WorkerRegistry,
        event_bus: Any = None,
        agent_runtime: Any = None,
        workflow_engine: Any = None,
        job_scheduler: Any = None,
    ) -> None:
        self._registry = registry
        self._event_bus = event_bus
        self._agent_runtime = agent_runtime
        self._workflow_engine = workflow_engine
        self._job_scheduler = job_scheduler
        self._assignments: dict[str, WorkerAssignment] = {}
        self._log = get_logger("eaip.workforce.orchestrator")

    async def assign(self, worker_id: str, task: str) -> WorkerAssignment:
        """Assign a task to a specific worker.

        Args:
            worker_id: The worker to assign to.
            task: The task description.

        Returns:
            The created WorkerAssignment.

        Raises:
            WorkerNotFoundError: If the worker is not registered.
            WorkerBusyError: If the worker is at max capacity.
        """
        definition = self._registry.get_worker(worker_id)

        current_active = self._registry.active_count(worker_id)
        if current_active >= definition.max_concurrent_runs:
            raise WorkerBusyError(worker_id, definition.max_concurrent_runs)

        assignment = WorkerAssignment(
            id=str(uuid.uuid4()),
            worker_id=worker_id,
            task_description=task,
            status=AssignmentStatus.PENDING,
        )
        self._assignments[assignment.id] = assignment
        self._registry.increment_active(worker_id)

        self._log.info(
            "assignment.created",
            assignment_id=assignment.id,
            worker_id=worker_id,
        )
        self._publish(
            WorkerAssigned(
                assignment_id=assignment.id,
                worker_id=worker_id,
                task_description=task,
            ),
        )
        return assignment

    async def assign_best_worker(
        self,
        task: str,
        required_type: WorkerType | None = None,
    ) -> WorkerAssignment:
        """Auto-assign a task to the best available worker.

        Selects the worker with the lowest active count among those matching
        the optional type filter.

        Args:
            task: The task description.
            required_type: Optional worker type requirement.

        Returns:
            The created WorkerAssignment.

        Raises:
            WorkforceError: If no workers are available.
        """
        candidates = self._registry.list_workers(worker_type=required_type)
        if not candidates:
            raise WorkerNotFoundError("no workers matching type")

        # Pick the worker with the fewest active runs.
        best: WorkerDefinition | None = None
        best_active = -1
        for candidate in candidates:
            active = self._registry.active_count(candidate.id)
            if active < candidate.max_concurrent_runs:
                if best is None or active < best_active:
                    best = candidate
                    best_active = active

        if best is None:
            raise WorkerBusyError("all", 0)

        return await self.assign(best.id, task)

    async def execute_assignment(self, assignment: WorkerAssignment) -> WorkerAssignment:
        """Execute a worker assignment via the appropriate runtime.

        Dispatches to AgentRuntime, WorkflowEngine, or JobScheduler based on
        the worker's type.

        Args:
            assignment: The assignment to execute.

        Returns:
            The completed WorkerAssignment.

        Raises:
            AssignmentError: If execution fails.
        """
        datetime.now()
        running = assignment.model_copy(update={"status": AssignmentStatus.RUNNING})
        self._assignments[assignment.id] = running

        try:
            definition = self._registry.get_worker(assignment.worker_id)
        except WorkerNotFoundError:
            return await self._fail_assignment(assignment, "worker not found")

        t0 = time.monotonic()
        try:
            result = await self._dispatch(definition, assignment)
            elapsed = time.monotonic() - t0
            completed = assignment.model_copy(
                update={
                    "status": AssignmentStatus.COMPLETED,
                    "result": result,
                    "completed_at": datetime.now(),
                },
            )
            self._assignments[assignment.id] = completed
            self._registry.decrement_active(assignment.worker_id)
            self._log.info(
                "assignment.completed",
                assignment_id=assignment.id,
                duration_ms=round(elapsed * 1000, 1),
            )
            self._publish(
                WorkerAssignmentCompleted(
                    assignment_id=assignment.id,
                    worker_id=assignment.worker_id,
                    result=result,
                    duration_ms=elapsed * 1000,
                ),
            )
            return completed
        except Exception as exc:
            elapsed = time.monotonic() - t0
            return await self._fail_assignment(assignment, str(exc), elapsed)
        finally:
            self._registry.decrement_active(assignment.worker_id)

    async def _dispatch(self, definition: WorkerDefinition, assignment: WorkerAssignment) -> str:
        if definition.worker_type is WorkerType.AGENT:
            if self._agent_runtime is None:
                raise AssignmentError(assignment.id, "agent runtime not available")
            run = await self._agent_runtime.create_run(
                definition.agent_id, assignment.task_description
            )
            result = await self._agent_runtime.start_run(run.id)
            return cast(str, result.result)

        if definition.worker_type is WorkerType.WORKFLOW:
            if self._workflow_engine is None:
                raise AssignmentError(assignment.id, "workflow engine not available")
            run = await self._workflow_engine.start(
                workflow_id=definition.workflow_id,
                context={"task": assignment.task_description},
            )
            return run.result if run else ""

        if definition.worker_type is WorkerType.JOB:
            if self._job_scheduler is None:
                raise AssignmentError(assignment.id, "job scheduler not available")
            result = await self._job_scheduler.execute_job(
                job_id=definition.job_id,
                run_id=assignment.run_id,
            )
            return cast(str, result.result)

        raise AssignmentError(assignment.id, f"unknown worker type: {definition.worker_type}")

    async def _fail_assignment(
        self,
        assignment: WorkerAssignment,
        error: str,
        elapsed: float = 0.0,
    ) -> WorkerAssignment:
        failed = assignment.model_copy(
            update={
                "status": AssignmentStatus.FAILED,
                "error": error,
                "completed_at": datetime.now(),
            },
        )
        self._assignments[assignment.id] = failed
        self._log.error("assignment.failed", assignment_id=assignment.id, error=error)
        self._publish(
            WorkerAssignmentFailed(
                assignment_id=assignment.id,
                worker_id=assignment.worker_id,
                error=error,
            ),
        )
        return failed

    async def get_status(self, assignment_id: str) -> WorkerAssignment | None:
        """Get the current status of an assignment.

        Args:
            assignment_id: The assignment ID.

        Returns:
            The WorkerAssignment, or None if not found.
        """
        return self._assignments.get(assignment_id)

    async def cancel_assignment(self, assignment_id: str) -> WorkerAssignment | None:
        """Cancel a pending or running assignment.

        Args:
            assignment_id: The assignment ID.

        Returns:
            The cancelled WorkerAssignment, or None if not found.
        """
        assignment = self._assignments.get(assignment_id)
        if assignment is None:
            return None
        if assignment.status in (AssignmentStatus.COMPLETED, AssignmentStatus.FAILED):
            return assignment
        cancelled = assignment.model_copy(
            update={
                "status": AssignmentStatus.FAILED,
                "error": "cancelled",
                "completed_at": datetime.now(),
            },
        )
        self._assignments[assignment_id] = cancelled
        self._registry.decrement_active(assignment.worker_id)
        return cancelled

    def list_assignments(
        self,
        worker_id: str | None = None,
        status: AssignmentStatus | None = None,
    ) -> list[WorkerAssignment]:
        """List assignments, optionally filtered by worker ID or status.

        Args:
            worker_id: Optional worker ID filter.
            status: Optional status filter.

        Returns:
            A list of WorkerAssignments.
        """
        results = list(self._assignments.values())
        if worker_id is not None:
            results = [a for a in results if a.worker_id == worker_id]
        if status is not None:
            results = [a for a in results if a.status is status]
        return results

    def get_metrics(self) -> WorkforceMetrics:
        """Compute workforce metrics from current assignment state.

        Returns:
            A WorkforceMetrics snapshot.
        """
        total = len(self._assignments)
        active = sum(1 for a in self._assignments.values() if a.status is AssignmentStatus.RUNNING)
        completed = sum(
            1 for a in self._assignments.values() if a.status is AssignmentStatus.COMPLETED
        )
        failed = sum(1 for a in self._assignments.values() if a.status is AssignmentStatus.FAILED)
        durations = [
            (a.completed_at - a.assigned_at).total_seconds() * 1000
            for a in self._assignments.values()
            if a.completed_at is not None and a.assigned_at is not None
        ]
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        return WorkforceMetrics(
            total_assignments=total,
            active_assignments=active,
            completed_assignments=completed,
            failed_assignments=failed,
            avg_duration_ms=avg_duration,
            workers_registered=len(self._registry.list_workers()),
        )

    def _publish(self, event: Any) -> None:
        if self._event_bus is not None:
            try:
                self._event_bus.publish(event)
            except Exception:
                self._log.warning("event.publish.failed", event_type=type(event).__name__)


__all__ = ["WorkforceOrchestrator"]
