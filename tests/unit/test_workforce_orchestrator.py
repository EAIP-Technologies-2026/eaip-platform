"""Tests for WorkforceOrchestrator."""

from __future__ import annotations

import pytest

from eaip.workforce.exceptions import WorkerBusyError, WorkerNotFoundError
from eaip.workforce.models import (
    AssignmentStatus,
    WorkerDefinition,
    WorkerType,
    WorkforceMetrics,
)
from eaip.workforce.orchestrator import WorkforceOrchestrator
from eaip.workforce.worker import WorkerRegistry


class TestWorkforceOrchestrator:
    @pytest.fixture
    def registry(self) -> WorkerRegistry:
        reg = WorkerRegistry()
        reg.register_worker(
            WorkerDefinition(
                id="w1", name="Worker 1", worker_type=WorkerType.AGENT, max_concurrent_runs=2
            ),
        )
        reg.register_worker(
            WorkerDefinition(
                id="w2", name="Worker 2", worker_type=WorkerType.AGENT, max_concurrent_runs=1
            ),
        )
        reg.register_worker(
            WorkerDefinition(
                id="w3", name="Workflow 1", worker_type=WorkerType.WORKFLOW, max_concurrent_runs=3
            ),
        )
        return reg

    @pytest.fixture
    def orchestrator(self, registry: WorkerRegistry) -> WorkforceOrchestrator:
        return WorkforceOrchestrator(registry=registry)

    async def test_assign(self, orchestrator: WorkforceOrchestrator) -> None:
        a = await orchestrator.assign("w1", "Do the thing")
        assert a.worker_id == "w1"
        assert a.task_description == "Do the thing"
        assert a.status is AssignmentStatus.PENDING
        assert a.id is not None

    async def test_assign_worker_not_found(self, orchestrator: WorkforceOrchestrator) -> None:
        with pytest.raises(WorkerNotFoundError):
            await orchestrator.assign("nonexistent", "task")

    async def test_assign_worker_busy(self, orchestrator: WorkforceOrchestrator) -> None:
        await orchestrator.assign("w2", "Task 1")
        with pytest.raises(WorkerBusyError):
            await orchestrator.assign("w2", "Task 2")

    async def test_assign_worker_at_capacity(self, orchestrator: WorkforceOrchestrator) -> None:
        await orchestrator.assign("w1", "Task 1")
        await orchestrator.assign("w1", "Task 2")
        with pytest.raises(WorkerBusyError):
            await orchestrator.assign("w1", "Task 3")

    async def test_assign_best_worker(self, orchestrator: WorkforceOrchestrator) -> None:
        a = await orchestrator.assign_best_worker("Best task")
        assert a.worker_id in ("w1", "w2", "w3")
        assert a.task_description == "Best task"

    async def test_assign_best_worker_by_type(self, orchestrator: WorkforceOrchestrator) -> None:
        a = await orchestrator.assign_best_worker(
            "Workflow task", required_type=WorkerType.WORKFLOW
        )
        assert a.worker_id == "w3"

    async def test_assign_best_worker_no_candidates(
        self, orchestrator: WorkforceOrchestrator
    ) -> None:
        with pytest.raises(WorkerNotFoundError):
            await orchestrator.assign_best_worker("task", required_type=WorkerType.JOB)

    async def test_assign_best_worker_all_busy(self, registry: WorkerRegistry) -> None:
        # Register a worker with max_concurrent=0 to test the all-busy path
        registry.register_worker(
            WorkerDefinition(
                id="w_busy", name="Always Busy", worker_type=WorkerType.JOB, max_concurrent_runs=0
            ),
        )
        orch = WorkforceOrchestrator(registry=registry)
        with pytest.raises(WorkerBusyError):
            await orch.assign_best_worker("task", required_type=WorkerType.JOB)

    async def test_get_status(self, orchestrator: WorkforceOrchestrator) -> None:
        a = await orchestrator.assign("w1", "Check status")
        result = await orchestrator.get_status(a.id)
        assert result is not None
        assert result.id == a.id
        assert result.status is AssignmentStatus.PENDING

    async def test_get_status_not_found(self, orchestrator: WorkforceOrchestrator) -> None:
        result = await orchestrator.get_status("nonexistent")
        assert result is None

    async def test_cancel_assignment(self, orchestrator: WorkforceOrchestrator) -> None:
        a = await orchestrator.assign("w1", "Cancel me")
        cancelled = await orchestrator.cancel_assignment(a.id)
        assert cancelled is not None
        assert cancelled.status is AssignmentStatus.FAILED
        assert cancelled.error == "cancelled"

    async def test_cancel_assignment_not_found(self, orchestrator: WorkforceOrchestrator) -> None:
        result = await orchestrator.cancel_assignment("nonexistent")
        assert result is None

    async def test_cancel_completed_assignment(self, orchestrator: WorkforceOrchestrator) -> None:
        a = await orchestrator.assign("w1", "Quick task")
        # Simulate completion by updating directly
        completed = a.model_copy(update={"status": AssignmentStatus.COMPLETED})
        orchestrator._assignments[a.id] = completed
        result = await orchestrator.cancel_assignment(a.id)
        assert result is not None
        # Should return unchanged since already completed
        assert result.status is AssignmentStatus.COMPLETED

    async def test_list_assignments(self, orchestrator: WorkforceOrchestrator) -> None:
        await orchestrator.assign("w1", "Task 1")
        await orchestrator.assign("w2", "Task 2")
        all_assignments = orchestrator.list_assignments()
        assert len(all_assignments) == 2

    async def test_list_assignments_by_worker(self, orchestrator: WorkforceOrchestrator) -> None:
        await orchestrator.assign("w1", "Task 1")
        await orchestrator.assign("w1", "Task 2")
        await orchestrator.assign("w2", "Task 3")
        w1_assignments = orchestrator.list_assignments(worker_id="w1")
        assert len(w1_assignments) == 2
        w2_assignments = orchestrator.list_assignments(worker_id="w2")
        assert len(w2_assignments) == 1

    async def test_list_assignments_by_status(self, orchestrator: WorkforceOrchestrator) -> None:
        a = await orchestrator.assign("w1", "Task")
        await orchestrator.cancel_assignment(a.id)
        failed = orchestrator.list_assignments(status=AssignmentStatus.FAILED)
        assert len(failed) == 1
        pending = orchestrator.list_assignments(status=AssignmentStatus.PENDING)
        assert len(pending) == 0

    async def test_get_metrics(self, orchestrator: WorkforceOrchestrator) -> None:
        metrics = orchestrator.get_metrics()
        assert isinstance(metrics, WorkforceMetrics)
        assert metrics.total_assignments == 0
        assert metrics.workers_registered == 3

    async def test_get_metrics_with_assignments(self, orchestrator: WorkforceOrchestrator) -> None:
        await orchestrator.assign("w1", "Task 1")
        await orchestrator.assign("w2", "Task 2")
        metrics = orchestrator.get_metrics()
        assert metrics.total_assignments == 2
        assert metrics.active_assignments == 0
        assert metrics.completed_assignments == 0
        assert metrics.failed_assignments == 0
        assert metrics.workers_registered == 3
