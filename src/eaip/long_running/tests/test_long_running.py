"""Tests for long-running workflow models, events, exceptions, and service."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from eaip.events.event import DomainEvent
from eaip.long_running.events import (
    WorkflowCancelled,
    WorkflowCheckpointCreated,
    WorkflowCheckpointRestored,
    WorkflowContinuationTriggered,
    WorkflowExecutionCompleted,
    WorkflowExecutionFailed,
    WorkflowExecutionStarted,
    WorkflowHeartbeatReceived,
    WorkflowPausedForDuration,
    WorkflowResumedFromCheckpoint,
    WorkflowScheduled,
    WorkflowStatePersisted,
    WorkflowStateRecovered,
)
from eaip.long_running.exceptions import (
    LongRunningError,
    WorkflowCheckpointError,
    WorkflowContinuationError,
    WorkflowExecutionTimeoutError,
    WorkflowHeartbeatTimeoutError,
    WorkflowNotFoundError,
    WorkflowRecoveryError,
    WorkflowStatePersistenceError,
)
from eaip.long_running.health import LongRunningHealthCheck
from eaip.long_running.integration import LongRunningRuntimeModule
from eaip.long_running.models import (
    LongRunningWorkflow,
    WorkflowCheckpoint,
    WorkflowContinuationToken,
    WorkflowExecutionPlan,
    WorkflowPersistenceConfig,
    WorkflowRecoveryStrategy,
    WorkflowSnapshot,
    WorkflowState,
    WorkflowStatus,
)
from eaip.long_running.service import LongRunningService

# ─── Model Tests ────────────────────────────────────────────────────────────────


class TestWorkflowState:
    def test_defaults(self) -> None:
        s = WorkflowState(workflow_id="wf_1")
        assert s.workflow_id == "wf_1"
        assert s.status == WorkflowStatus.PENDING
        assert s.attempt == 0
        assert s.error is None

    def test_frozen(self) -> None:
        s = WorkflowState(workflow_id="wf_1")
        with pytest.raises(ValidationError):
            s.status = WorkflowStatus.RUNNING

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            WorkflowState.model_validate({"workflow_id": "wf_1", "unknown_field": True})

    def test_all_statuses(self) -> None:
        for st in WorkflowStatus:
            s = WorkflowState(workflow_id="wf_1", status=st)
            assert s.status == st

    def test_completed_state(self) -> None:
        now = datetime.now(UTC)
        s = WorkflowState(
            workflow_id="wf_1",
            status=WorkflowStatus.COMPLETED,
            completed_at=now,
            error=None,
        )
        assert s.completed_at == now
        assert s.error is None


class TestWorkflowCheckpoint:
    def test_minimal(self) -> None:
        state = WorkflowState(workflow_id="wf_1")
        snapshot = WorkflowSnapshot(state=state)
        cp = WorkflowCheckpoint(id="cp_1", workflow_id="wf_1", snapshot=snapshot)
        assert cp.id == "cp_1"
        assert cp.step_id == ""

    def test_frozen(self) -> None:
        state = WorkflowState(workflow_id="wf_1")
        snapshot = WorkflowSnapshot(state=state)
        cp = WorkflowCheckpoint(id="cp_1", workflow_id="wf_1", snapshot=snapshot)
        with pytest.raises(ValidationError):
            cp.id = "changed"

    def test_expires_at(self) -> None:
        state = WorkflowState(workflow_id="wf_1")
        snapshot = WorkflowSnapshot(state=state)
        future = datetime.now(UTC)
        cp = WorkflowCheckpoint(id="cp_1", workflow_id="wf_1", snapshot=snapshot, expires_at=future)
        assert cp.expires_at == future


class TestWorkflowSnapshot:
    def test_defaults(self) -> None:
        state = WorkflowState(workflow_id="wf_1")
        snap = WorkflowSnapshot(state=state)
        assert snap.context == {}
        assert snap.step_results == {}
        assert snap.variables == {}

    def test_with_data(self) -> None:
        state = WorkflowState(workflow_id="wf_1", status=WorkflowStatus.RUNNING)
        snap = WorkflowSnapshot(
            state=state,
            context={"key": "val"},
            step_results={"step_1": "ok"},
            variables={"var": 42},
        )
        assert snap.context["key"] == "val"
        assert snap.step_results["step_1"] == "ok"
        assert snap.variables["var"] == 42


class TestWorkflowPersistenceConfig:
    def test_defaults(self) -> None:
        c = WorkflowPersistenceConfig()
        assert c.enabled is True
        assert c.store_type == "memory"
        assert c.persist_after_each_step is True

    def test_custom(self) -> None:
        c = WorkflowPersistenceConfig(
            enabled=False,
            store_type="redis",
            checkpoint_ttl_seconds=3600.0,
            max_checkpoints=10,
            compression_enabled=True,
            encryption_enabled=True,
        )
        assert c.enabled is False
        assert c.store_type == "redis"
        assert c.max_checkpoints == 10


class TestWorkflowExecutionPlan:
    def test_defaults(self) -> None:
        p = WorkflowExecutionPlan(workflow_id="wf_1")
        assert p.recovery_strategy == WorkflowRecoveryStrategy.RESUME
        assert p.heartbeat_interval_seconds == 30.0
        assert p.max_retries == 3

    def test_custom(self) -> None:
        p = WorkflowExecutionPlan(
            workflow_id="wf_1",
            steps=("step_1", "step_2", "step_3"),
            recovery_strategy=WorkflowRecoveryStrategy.RESTART,
            execution_timeout_seconds=3600.0,
            max_retries=5,
        )
        assert len(p.steps) == 3
        assert p.recovery_strategy == WorkflowRecoveryStrategy.RESTART
        assert p.execution_timeout_seconds == 3600.0


class TestWorkflowContinuationToken:
    def test_defaults(self) -> None:
        t = WorkflowContinuationToken(token="tok_1", workflow_id="wf_1")
        assert t.next_step_id == ""
        assert t.context == {}

    def test_frozen(self) -> None:
        t = WorkflowContinuationToken(token="tok_1", workflow_id="wf_1")
        with pytest.raises(ValidationError):
            t.token = "changed"


class TestLongRunningWorkflow:
    def test_minimal(self) -> None:
        wf = LongRunningWorkflow(id="wf_1", name="Test Workflow")
        assert wf.description == ""
        assert wf.version == "0.1.0"
        assert wf.tags == ()

    def test_with_state(self) -> None:
        state = WorkflowState(workflow_id="wf_1", status=WorkflowStatus.RUNNING)
        wf = LongRunningWorkflow(id="wf_1", name="Running Workflow", state=state)
        assert wf.state.status == WorkflowStatus.RUNNING

    def test_frozen(self) -> None:
        wf = LongRunningWorkflow(id="wf_1", name="Test")
        with pytest.raises(ValidationError):
            wf.name = "Changed"


class TestWorkflowRecoveryStrategy:
    def test_all_values(self) -> None:
        assert WorkflowRecoveryStrategy.RESTART.value == "restart"
        assert WorkflowRecoveryStrategy.RESUME.value == "resume"
        assert WorkflowRecoveryStrategy.SKIP_COMPLETED.value == "skip_completed"
        assert WorkflowRecoveryStrategy.ROLLBACK.value == "rollback"


class TestWorkflowStatus:
    def test_all_values(self) -> None:
        assert WorkflowStatus.PENDING.value == "pending"
        assert WorkflowStatus.CHECKPOINTED.value == "checkpointed"
        assert WorkflowStatus.CANCELLED.value == "cancelled"
        assert WorkflowStatus.TIMED_OUT.value == "timed_out"


# ─── Event Tests ────────────────────────────────────────────────────────────────


class TestWorkflowScheduled:
    def test_event_type(self) -> None:
        event = WorkflowScheduled(workflow_id="wf_1", workflow_name="Test")
        assert event.event_type == "eaip.long_running.scheduled"
        assert isinstance(event, DomainEvent)


class TestWorkflowExecutionStarted:
    def test_event_type(self) -> None:
        event = WorkflowExecutionStarted(workflow_id="wf_1", workflow_name="Test")
        assert event.event_type == "eaip.long_running.execution.started"


class TestWorkflowCheckpointCreated:
    def test_event_type(self) -> None:
        event = WorkflowCheckpointCreated(workflow_id="wf_1")
        assert event.event_type == "eaip.long_running.checkpoint.created"


class TestWorkflowCheckpointRestored:
    def test_event_type(self) -> None:
        event = WorkflowCheckpointRestored(
            workflow_id="wf_1", checkpoint_id="cp_1", step_id="step_1"
        )
        assert event.event_type == "eaip.long_running.checkpoint.restored"
        assert event.checkpoint_id == "cp_1"


class TestWorkflowPausedForDuration:
    def test_event_type(self) -> None:
        event = WorkflowPausedForDuration(
            workflow_id="wf_1", workflow_name="Test", duration_seconds=60.0
        )
        assert event.event_type == "eaip.long_running.paused_for_duration"
        assert event.duration_seconds == 60.0


class TestWorkflowResumedFromCheckpoint:
    def test_event_type(self) -> None:
        event = WorkflowResumedFromCheckpoint(
            workflow_id="wf_1", checkpoint_id="cp_1", step_id="step_1", attempt=2
        )
        assert event.event_type == "eaip.long_running.resumed_from_checkpoint"
        assert event.attempt == 2


class TestWorkflowHeartbeatReceived:
    def test_event_type(self) -> None:
        event = WorkflowHeartbeatReceived(workflow_id="wf_1", step_id="step_1", progress=0.5)
        assert event.event_type == "eaip.long_running.heartbeat.received"
        assert event.progress == 0.5


class TestWorkflowStatePersisted:
    def test_event_type(self) -> None:
        event = WorkflowStatePersisted(workflow_id="wf_1")
        assert event.event_type == "eaip.long_running.state.persisted"


class TestWorkflowStateRecovered:
    def test_event_type(self) -> None:
        event = WorkflowStateRecovered(workflow_id="wf_1")
        assert event.event_type == "eaip.long_running.state.recovered"
        assert event.recovered_step_id == ""


class TestWorkflowExecutionCompleted:
    def test_event_type(self) -> None:
        event = WorkflowExecutionCompleted(workflow_id="wf_1", workflow_name="Test", result="done")
        assert event.event_type == "eaip.long_running.execution.completed"
        assert event.result == "done"


class TestWorkflowExecutionFailed:
    def test_event_type(self) -> None:
        event = WorkflowExecutionFailed(
            workflow_id="wf_1", workflow_name="Test", error="oops", will_retry=True
        )
        assert event.event_type == "eaip.long_running.execution.failed"
        assert event.error == "oops"
        assert event.will_retry is True


class TestWorkflowCancelled:
    def test_event_type(self) -> None:
        event = WorkflowCancelled(workflow_id="wf_1", workflow_name="Test", reason="user request")
        assert event.event_type == "eaip.long_running.cancelled"
        assert event.reason == "user request"


class TestWorkflowContinuationTriggered:
    def test_event_type(self) -> None:
        event = WorkflowContinuationTriggered(
            workflow_id="wf_1", token="tok_1", next_step_id="step_2"
        )
        assert event.event_type == "eaip.long_running.continuation.triggered"
        assert event.token == "tok_1"


class TestAllEventsAreDomainEvents:
    def test_all_are_domain_events(self) -> None:
        events = [
            WorkflowScheduled(workflow_id="wf_1", workflow_name="T"),
            WorkflowExecutionStarted(workflow_id="wf_1", workflow_name="T"),
            WorkflowCheckpointCreated(workflow_id="wf_1"),
            WorkflowCheckpointRestored(workflow_id="wf_1", checkpoint_id="cp_1", step_id="s1"),
            WorkflowPausedForDuration(workflow_id="wf_1", workflow_name="T", duration_seconds=10.0),
            WorkflowResumedFromCheckpoint(
                workflow_id="wf_1", checkpoint_id="cp_1", step_id="s1", attempt=1
            ),
            WorkflowHeartbeatReceived(workflow_id="wf_1", step_id="s1", progress=0.0),
            WorkflowStatePersisted(workflow_id="wf_1"),
            WorkflowStateRecovered(workflow_id="wf_1"),
            WorkflowExecutionCompleted(workflow_id="wf_1", workflow_name="T"),
            WorkflowExecutionFailed(workflow_id="wf_1", workflow_name="T", error="e"),
            WorkflowCancelled(workflow_id="wf_1", workflow_name="T", reason="r"),
            WorkflowContinuationTriggered(workflow_id="wf_1", token="t", next_step_id="s2"),
        ]
        for event in events:
            assert isinstance(event, DomainEvent)
            assert event.occurred_at is not None


# ─── Exception Tests ────────────────────────────────────────────────────────────


class TestExceptions:
    def test_long_running_error(self) -> None:
        e = LongRunningError("something went wrong")
        assert isinstance(e, LongRunningError)
        assert str(e) == "something went wrong"

    def test_workflow_not_found_error(self) -> None:
        e = WorkflowNotFoundError("wf_1")
        assert e.workflow_id == "wf_1"
        assert "wf_1" in str(e)

    def test_workflow_state_persistence_error(self) -> None:
        e = WorkflowStatePersistenceError("wf_1", "write failed")
        assert e.workflow_id == "wf_1"

    def test_workflow_recovery_error(self) -> None:
        e = WorkflowRecoveryError("wf_1", "no checkpoints")
        assert e.workflow_id == "wf_1"

    def test_workflow_checkpoint_error(self) -> None:
        e = WorkflowCheckpointError("wf_1", "limit reached")
        assert e.workflow_id == "wf_1"

    def test_workflow_continuation_error(self) -> None:
        e = WorkflowContinuationError("wf_1", "invalid token")
        assert e.workflow_id == "wf_1"

    def test_heartbeat_timeout_error(self) -> None:
        e = WorkflowHeartbeatTimeoutError("wf_1", 30.0)
        assert e.timeout_seconds == 30.0
        assert "30" in str(e)

    def test_execution_timeout_error(self) -> None:
        e = WorkflowExecutionTimeoutError("wf_1", 3600.0)
        assert e.timeout_seconds == 3600.0


# ─── Service Tests ──────────────────────────────────────────────────────────────


class TestLongRunningService:
    @pytest.fixture
    def service(self) -> LongRunningService:
        return LongRunningService()

    async def test_schedule_workflow(self, service: LongRunningService) -> None:
        event = await service.schedule("wf_1", "Test Workflow")
        assert event.workflow_id == "wf_1"
        assert event.workflow_name == "Test Workflow"
        wf = await service.get_workflow("wf_1")
        assert wf.state.status == WorkflowStatus.PENDING

    async def test_schedule_with_plan(self, service: LongRunningService) -> None:
        plan = WorkflowExecutionPlan(
            workflow_id="wf_1",
            recovery_strategy=WorkflowRecoveryStrategy.RESTART,
            max_retries=5,
        )
        event = await service.schedule("wf_1", "Planned", plan=plan)
        assert event.plan is not None
        assert event.plan.max_retries == 5

    async def test_execute_workflow(self, service: LongRunningService) -> None:
        await service.schedule("wf_1", "Test")
        event = await service.execute("wf_1", step_id="step_1")
        assert event.workflow_id == "wf_1"
        assert event.step_id == "step_1"
        wf = await service.get_workflow("wf_1")
        assert wf.state.status == WorkflowStatus.RUNNING
        assert wf.state.attempt == 1

    async def test_execute_not_found(self, service: LongRunningService) -> None:
        with pytest.raises(WorkflowNotFoundError):
            await service.execute("nonexistent")

    async def test_execute_with_context(self, service: LongRunningService) -> None:
        await service.schedule("wf_1", "Test")
        await service.execute("wf_1", context={"key": "val"})
        wf = await service.get_workflow("wf_1")
        assert wf.state.context.get("key") == "val"

    async def test_checkpoint_workflow(self, service: LongRunningService) -> None:
        await service.schedule("wf_1", "Test")
        await service.execute("wf_1", step_id="step_1")
        event = await service.checkpoint(
            "wf_1",
            checkpoint_id="cp_1",
            step_id="step_1",
            snapshot_context={"progress": "half"},
            variables={"count": 42},
        )
        assert event.checkpoint is not None
        assert event.checkpoint.id == "cp_1"
        wf = await service.get_workflow("wf_1")
        assert len(wf.checkpoints) == 1

    async def test_checkpoint_not_found(self, service: LongRunningService) -> None:
        with pytest.raises(WorkflowNotFoundError):
            await service.checkpoint("nonexistent", "cp_1")

    async def test_checkpoint_limit(self) -> None:
        config = WorkflowPersistenceConfig(max_checkpoints=1)
        svc = LongRunningService(persistence_config=config)
        await svc.schedule("wf_1", "Test")
        await svc.execute("wf_1")
        await svc.checkpoint("wf_1", "cp_1", step_id="step_1")
        with pytest.raises(WorkflowCheckpointError):
            await svc.checkpoint("wf_1", "cp_2", step_id="step_1")

    async def test_recover_restart(self, service: LongRunningService) -> None:
        await service.schedule("wf_1", "Test")
        await service.execute("wf_1")
        event = await service.recover("wf_1", strategy=WorkflowRecoveryStrategy.RESTART)
        assert event.strategy == WorkflowRecoveryStrategy.RESTART
        assert event.recovered_step_id == ""

    async def test_recover_resume(self, service: LongRunningService) -> None:
        await service.schedule("wf_1", "Test")
        await service.execute("wf_1", step_id="step_1")
        await service.checkpoint("wf_1", "cp_1", step_id="step_1")
        event = await service.recover("wf_1", strategy=WorkflowRecoveryStrategy.RESUME)
        assert event.strategy == WorkflowRecoveryStrategy.RESUME
        assert event.recovered_step_id == "step_1"

    async def test_recover_not_found(self, service: LongRunningService) -> None:
        with pytest.raises(WorkflowNotFoundError):
            await service.recover("nonexistent")

    async def test_complete_workflow(self, service: LongRunningService) -> None:
        await service.schedule("wf_1", "Test")
        await service.execute("wf_1")
        event = await service.complete("wf_1", result="success")
        assert event.status == WorkflowStatus.COMPLETED
        assert event.result == "success"
        wf = await service.get_workflow("wf_1")
        assert wf.state.status == WorkflowStatus.COMPLETED

    async def test_fail_workflow(self, service: LongRunningService) -> None:
        await service.schedule("wf_1", "Test")
        await service.execute("wf_1")
        event = await service.fail("wf_1", error="processing error", will_retry=True)
        assert event.error == "processing error"
        assert event.will_retry is True
        wf = await service.get_workflow("wf_1")
        assert wf.state.status == WorkflowStatus.FAILED

    async def test_full_lifecycle(self, service: LongRunningService) -> None:
        await service.schedule("wf_1", "Lifecycle")
        await service.execute("wf_1", step_id="step_1")
        await service.checkpoint("wf_1", "cp_1", step_id="step_1")
        await service.recover("wf_1", strategy=WorkflowRecoveryStrategy.RESUME)
        await service.complete("wf_1", result="done")
        wf = await service.get_workflow("wf_1")
        assert wf.state.status == WorkflowStatus.COMPLETED
        assert len(wf.checkpoints) == 1


# ─── Health Check Tests ─────────────────────────────────────────────────────────


class TestLongRunningHealthCheck:
    async def test_healthy(self) -> None:
        service = LongRunningService()
        await service.schedule("wf_1", "Test")
        check = LongRunningHealthCheck(service=service)
        report = await check.check()
        assert report.component == "long_running"
        assert report.status.value == "healthy"

    async def test_degraded_when_no_workflows(self) -> None:
        service = LongRunningService()
        check = LongRunningHealthCheck(service=service)
        report = await check.check()
        assert report.status.value == "degraded"
        assert "No long-running workflows" in report.message


# ─── Integration Tests ──────────────────────────────────────────────────────────


class TestLongRunningRuntimeModule:
    def test_module_name(self) -> None:
        module = LongRunningRuntimeModule()
        assert module.name == "long_running"

    def test_service_property(self) -> None:
        module = LongRunningRuntimeModule()
        assert module.service is not None
        assert isinstance(module.service, LongRunningService)

    def test_custom_service(self) -> None:
        service = LongRunningService()
        module = LongRunningRuntimeModule(service=service)
        assert module.service is service
