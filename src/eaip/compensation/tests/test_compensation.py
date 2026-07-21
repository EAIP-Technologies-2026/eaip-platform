"""Tests for compensation models, events, exceptions, and service."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.compensation.events import (
    CompensationCompleted,
    CompensationFailed,
    CompensationPlanCreated,
    CompensationPlanExecuted,
    CompensationPlanFailed,
    CompensationPlanRolledBack,
    CompensationRolledBack,
    CompensationStarted,
    CompensationStepCompleted,
    CompensationStepFailed,
    CompensationStepSkipped,
    CompensationStepStarted,
    CompensationTransactionCompleted,
    CompensationTransactionCreated,
)
from eaip.compensation.exceptions import (
    CompensationConfigError,
    CompensationError,
    CompensationExecutionError,
    CompensationPlanNotFoundError,
    CompensationPlanValidationError,
    CompensationRollbackError,
    CompensationStepError,
)
from eaip.compensation.models import (
    CompensableStep,
    CompensableWorkflow,
    CompensationAction,
    CompensationConfig,
    CompensationPlan,
    CompensationResult,
    CompensationScope,
    CompensationStatus,
    CompensationStep,
    CompensationStrategy,
    CompensationTransaction,
)
from eaip.compensation.service import CompensationService
from eaip.events.event import DomainEvent

# ── Models ──────────────────────────────────────────────────────────


class TestCompensationStatus:
    def test_values(self) -> None:
        assert CompensationStatus.PENDING.value == "pending"
        assert CompensationStatus.COMPENSATING.value == "compensating"
        assert CompensationStatus.COMPLETED.value == "completed"
        assert CompensationStatus.FAILED.value == "failed"
        assert CompensationStatus.SKIPPED.value == "skipped"
        assert CompensationStatus.ROLLED_BACK.value == "rolled_back"


class TestCompensationStrategy:
    def test_values(self) -> None:
        assert CompensationStrategy.SEQUENTIAL.value == "sequential"
        assert CompensationStrategy.PARALLEL.value == "parallel"
        assert CompensationStrategy.BEST_EFFORT.value == "best_effort"
        assert CompensationStrategy.FAIL_FAST.value == "fail_fast"


class TestCompensationAction:
    def test_defaults(self) -> None:
        a = CompensationAction(step_id="s1", action_type="rollback")
        assert a.step_id == "s1"
        assert a.payload == {}
        assert a.metadata == {}

    def test_frozen(self) -> None:
        a = CompensationAction(step_id="s1", action_type="rollback")
        with pytest.raises(ValidationError):
            a.step_id = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            CompensationAction.model_validate(
                {"step_id": "s1", "action_type": "x", "unknown": "bad"}
            )


class TestCompensationTransaction:
    def test_defaults(self) -> None:
        action = CompensationAction(step_id="s1", action_type="noop")
        t = CompensationTransaction(id="t1", plan_id="p1", step_id="s1", action=action)
        assert t.status == CompensationStatus.PENDING
        assert t.result == ""
        assert t.error is None

    def test_frozen(self) -> None:
        action = CompensationAction(step_id="s1", action_type="noop")
        t = CompensationTransaction(id="t1", plan_id="p1", step_id="s1", action=action)
        with pytest.raises(ValidationError):
            t.id = "changed"


class TestCompensationStep:
    def test_minimal(self) -> None:
        s = CompensationStep(id="s1", name="Step 1")
        assert s.description == ""
        assert s.status == CompensationStatus.PENDING
        assert s.actions == ()
        assert s.depends_on == ()
        assert s.timeout_seconds == 30.0

    def test_frozen(self) -> None:
        s = CompensationStep(id="s1", name="Step 1")
        with pytest.raises(ValidationError):
            s.name = "Changed"


class TestCompensationPlan:
    def test_minimal(self) -> None:
        p = CompensationPlan(id="p1", name="Plan 1", workflow_id="wf1")
        assert p.status == CompensationStatus.PENDING
        assert p.steps == ()
        assert p.strategy == CompensationStrategy.SEQUENTIAL
        assert p.scope == CompensationScope.PLAN

    def test_full(self) -> None:
        step = CompensationStep(id="s1", name="Step 1")
        p = CompensationPlan(
            id="p1",
            name="Plan 1",
            description="Test plan",
            workflow_id="wf1",
            workflow_name="Workflow 1",
            steps=(step,),
            strategy=CompensationStrategy.FAIL_FAST,
            scope=CompensationScope.WORKFLOW,
            metadata={"key": "value"},
        )
        assert len(p.steps) == 1
        assert p.strategy == CompensationStrategy.FAIL_FAST
        assert p.metadata["key"] == "value"

    def test_frozen(self) -> None:
        p = CompensationPlan(id="p1", name="Plan 1", workflow_id="wf1")
        with pytest.raises(ValidationError):
            p.name = "Changed"


class TestCompensationResult:
    def test_defaults(self) -> None:
        r = CompensationResult(plan_id="p1", status=CompensationStatus.COMPLETED)
        assert r.total_steps == 0
        assert r.duration_ms == 0.0
        assert r.error is None

    def test_frozen(self) -> None:
        r = CompensationResult(plan_id="p1", status=CompensationStatus.COMPLETED)
        with pytest.raises(ValidationError):
            r.plan_id = "changed"


class TestCompensationConfig:
    def test_defaults(self) -> None:
        c = CompensationConfig()
        assert c.default_strategy == CompensationStrategy.SEQUENTIAL
        assert c.default_timeout_seconds == 30.0
        assert c.max_retries == 3
        assert c.fail_on_first_error is True

    def test_custom(self) -> None:
        c = CompensationConfig(
            default_strategy=CompensationStrategy.FAIL_FAST,
            default_timeout_seconds=60.0,
            max_retries=5,
            fail_on_first_error=False,
        )
        assert c.default_strategy == CompensationStrategy.FAIL_FAST
        assert c.default_timeout_seconds == 60.0
        assert c.fail_on_first_error is False

    def test_frozen(self) -> None:
        c = CompensationConfig()
        with pytest.raises(ValidationError):
            c.max_retries = 10


class TestCompensableWorkflow:
    def test_minimal(self) -> None:
        w = CompensableWorkflow(id="wf1", name="Workflow 1")
        assert w.steps == ()
        assert w.compensation_plan_id is None
        assert w.metadata == {}


class TestCompensableStep:
    def test_minimal(self) -> None:
        s = CompensableStep(id="s1", name="Step 1")
        assert s.compensation_action is None
        assert s.critical is False
        assert s.timeout_seconds == 30.0


# ── Events ──────────────────────────────────────────────────────────


class TestCompensationPlanCreated:
    def test_event_type(self) -> None:
        plan = CompensationPlan(id="p1", name="Plan 1", workflow_id="wf1")
        event = CompensationPlanCreated(plan=plan)
        assert event.event_type == "eaip.compensation.plan.created"
        assert isinstance(event, DomainEvent)

    def test_plan_content(self) -> None:
        plan = CompensationPlan(id="p1", name="Plan 1", workflow_id="wf1")
        event = CompensationPlanCreated(plan=plan)
        assert event.plan.id == "p1"


class TestCompensationPlanExecuted:
    def test_event_type(self) -> None:
        plan = CompensationPlan(id="p1", name="Plan 1", workflow_id="wf1")
        event = CompensationPlanExecuted(plan=plan)
        assert event.event_type == "eaip.compensation.plan.executed"


class TestCompensationPlanFailed:
    def test_event_type(self) -> None:
        plan = CompensationPlan(id="p1", name="Plan 1", workflow_id="wf1")
        event = CompensationPlanFailed(plan=plan, error="oops")
        assert event.event_type == "eaip.compensation.plan.failed"
        assert event.error == "oops"


class TestCompensationPlanRolledBack:
    def test_event_type(self) -> None:
        plan = CompensationPlan(id="p1", name="Plan 1", workflow_id="wf1")
        event = CompensationPlanRolledBack(plan=plan)
        assert event.event_type == "eaip.compensation.plan.rolled_back"


class TestCompensationStarted:
    def test_event_type(self) -> None:
        event = CompensationStarted(plan_id="p1", plan_name="Plan 1")
        assert event.event_type == "eaip.compensation.started"


class TestCompensationStepStarted:
    def test_event_type(self) -> None:
        step = CompensationStep(id="s1", name="Step 1")
        event = CompensationStepStarted(plan_id="p1", step=step)
        assert event.event_type == "eaip.compensation.step.started"


class TestCompensationStepCompleted:
    def test_event_type(self) -> None:
        step = CompensationStep(id="s1", name="Step 1")
        event = CompensationStepCompleted(plan_id="p1", step=step, duration_ms=100.0)
        assert event.event_type == "eaip.compensation.step.completed"
        assert event.duration_ms == 100.0


class TestCompensationStepFailed:
    def test_event_type(self) -> None:
        step = CompensationStep(id="s1", name="Step 1")
        event = CompensationStepFailed(plan_id="p1", step=step, error="err")
        assert event.event_type == "eaip.compensation.step.failed"
        assert event.error == "err"


class TestCompensationStepSkipped:
    def test_event_type(self) -> None:
        step = CompensationStep(id="s1", name="Step 1")
        event = CompensationStepSkipped(plan_id="p1", step=step, reason="dependency_failed")
        assert event.event_type == "eaip.compensation.step.skipped"
        assert event.reason == "dependency_failed"


class TestCompensationCompleted:
    def test_event_type(self) -> None:
        event = CompensationCompleted(
            plan_id="p1",
            plan_name="Plan 1",
            total_steps=3,
            completed_steps=3,
            failed_steps=0,
            duration_ms=500.0,
        )
        assert event.event_type == "eaip.compensation.completed"
        assert event.total_steps == 3


class TestCompensationFailed:
    def test_event_type(self) -> None:
        event = CompensationFailed(plan_id="p1", plan_name="Plan 1", error="err")
        assert event.event_type == "eaip.compensation.failed"
        assert event.error == "err"


class TestCompensationRolledBack:
    def test_event_type(self) -> None:
        event = CompensationRolledBack(plan_id="p1", plan_name="Plan 1")
        assert event.event_type == "eaip.compensation.rolled_back"


class TestCompensationTransactionCreated:
    def test_event_type(self) -> None:
        action = CompensationAction(step_id="s1", action_type="noop")
        tx = CompensationTransaction(id="t1", plan_id="p1", step_id="s1", action=action)
        event = CompensationTransactionCreated(transaction=tx)
        assert event.event_type == "eaip.compensation.transaction.created"


class TestCompensationTransactionCompleted:
    def test_event_type(self) -> None:
        action = CompensationAction(step_id="s1", action_type="noop")
        tx = CompensationTransaction(
            id="t1",
            plan_id="p1",
            step_id="s1",
            action=action,
            status=CompensationStatus.COMPLETED,
        )
        event = CompensationTransactionCompleted(transaction=tx)
        assert event.event_type == "eaip.compensation.transaction.completed"


class TestAllEventsAreDomainEvents:
    def test_all_are_domain_events(self) -> None:
        plan = CompensationPlan(id="p1", name="Plan 1", workflow_id="wf1")
        step = CompensationStep(id="s1", name="Step 1")
        action = CompensationAction(step_id="s1", action_type="noop")
        tx = CompensationTransaction(id="t1", plan_id="p1", step_id="s1", action=action)

        events = [
            CompensationPlanCreated(plan=plan),
            CompensationPlanExecuted(plan=plan),
            CompensationPlanFailed(plan=plan, error="err"),
            CompensationPlanRolledBack(plan=plan),
            CompensationStarted(plan_id="p1", plan_name="Plan 1"),
            CompensationStepStarted(plan_id="p1", step=step),
            CompensationStepCompleted(plan_id="p1", step=step, duration_ms=1.0),
            CompensationStepFailed(plan_id="p1", step=step, error="err"),
            CompensationStepSkipped(plan_id="p1", step=step, reason="r"),
            CompensationCompleted(
                plan_id="p1",
                plan_name="Plan 1",
                total_steps=1,
                completed_steps=1,
                failed_steps=0,
                duration_ms=1.0,
            ),
            CompensationFailed(plan_id="p1", plan_name="Plan 1", error="err"),
            CompensationRolledBack(plan_id="p1", plan_name="Plan 1"),
            CompensationTransactionCreated(transaction=tx),
            CompensationTransactionCompleted(transaction=tx),
        ]
        for event in events:
            assert isinstance(event, DomainEvent)
            assert event.occurred_at is not None


# ── Exceptions ──────────────────────────────────────────────────────


class TestExceptions:
    def test_compensation_error_base(self) -> None:
        err = CompensationError("test error")
        assert "test error" in str(err)

    def test_plan_not_found(self) -> None:
        err = CompensationPlanNotFoundError("not found")
        assert "not found" in str(err)

    def test_execution_error(self) -> None:
        err = CompensationExecutionError("exec failed")
        assert "exec failed" in str(err)

    def test_step_error(self) -> None:
        err = CompensationStepError("step failed")
        assert "step failed" in str(err)

    def test_rollback_error(self) -> None:
        err = CompensationRollbackError("rollback failed")
        assert "rollback failed" in str(err)

    def test_config_error(self) -> None:
        err = CompensationConfigError("bad config")
        assert "bad config" in str(err)

    def test_validation_error(self) -> None:
        err = CompensationPlanValidationError("invalid")
        assert "invalid" in str(err)

    def test_with_context(self) -> None:
        err = CompensationPlanNotFoundError("not found", context={"plan_id": "p1"})
        assert err.context["plan_id"] == "p1"

    def test_with_cause(self) -> None:
        cause = ValueError("root cause")
        err = CompensationExecutionError("wrapped", cause=cause)
        assert err.__cause__ is cause

    def test_error_hierarchy(self) -> None:
        assert issubclass(CompensationPlanNotFoundError, CompensationError)
        assert issubclass(CompensationExecutionError, CompensationError)
        assert issubclass(CompensationStepError, CompensationError)
        assert issubclass(CompensationRollbackError, CompensationError)
        assert issubclass(CompensationConfigError, CompensationError)
        assert issubclass(CompensationPlanValidationError, CompensationError)
        assert issubclass(CompensationError, Exception)


# ── Service ─────────────────────────────────────────────────────────


class TestCompensationService:
    @pytest.fixture
    def service(self) -> CompensationService:
        return CompensationService()

    @pytest.fixture
    def sample_step(self) -> CompensationStep:
        action = CompensationAction(step_id="s1", action_type="noop")
        return CompensationStep(id="s1", name="Step 1", actions=(action,))

    async def test_create_plan(self, service: CompensationService) -> None:
        plan = await service.create_plan(
            name="Test Plan",
            workflow_id="wf1",
            workflow_name="Workflow 1",
        )
        assert plan.name == "Test Plan"
        assert plan.workflow_id == "wf1"
        assert plan.status == CompensationStatus.PENDING
        assert plan.id is not None

    async def test_create_plan_validation_empty_name(self, service: CompensationService) -> None:
        with pytest.raises(CompensationPlanValidationError):
            await service.create_plan(name="", workflow_id="wf1")

    async def test_create_plan_validation_empty_workflow_id(
        self, service: CompensationService
    ) -> None:
        with pytest.raises(CompensationPlanValidationError):
            await service.create_plan(name="Plan", workflow_id="")

    async def test_get_plan(self, service: CompensationService) -> None:
        plan = await service.create_plan(name="Plan", workflow_id="wf1")
        retrieved = await service.get_plan(plan.id)
        assert retrieved.id == plan.id

    async def test_get_plan_not_found(self, service: CompensationService) -> None:
        with pytest.raises(CompensationPlanNotFoundError):
            await service.get_plan("nonexistent")

    async def test_list_plans(self, service: CompensationService) -> None:
        await service.create_plan(name="Plan 1", workflow_id="wf1")
        await service.create_plan(name="Plan 2", workflow_id="wf1")
        plans = await service.list_plans()
        assert len(plans) == 2

    async def test_list_plans_by_workflow(self, service: CompensationService) -> None:
        await service.create_plan(name="Plan 1", workflow_id="wf1")
        await service.create_plan(name="Plan 2", workflow_id="wf2")
        wf1_plans = await service.list_plans(workflow_id="wf1")
        assert len(wf1_plans) == 1

    async def test_execute_plan_success(
        self, service: CompensationService, sample_step: CompensationStep
    ) -> None:
        plan = await service.create_plan(
            name="Plan",
            workflow_id="wf1",
            steps=(sample_step,),
        )
        result = await service.execute_plan(plan.id)
        assert result.status == CompensationStatus.COMPLETED
        assert result.total_steps == 1
        assert result.completed_steps == 1

    async def test_execute_plan_not_found(self, service: CompensationService) -> None:
        with pytest.raises(CompensationPlanNotFoundError):
            await service.execute_plan("nonexistent")

    async def test_rollback_plan(
        self, service: CompensationService, sample_step: CompensationStep
    ) -> None:
        plan = await service.create_plan(
            name="Plan",
            workflow_id="wf1",
            steps=(sample_step,),
        )
        await service.execute_plan(plan.id)
        result = await service.rollback_plan(plan.id)
        assert result.status == CompensationStatus.ROLLED_BACK

    async def test_rollback_pending_plan(self, service: CompensationService) -> None:
        plan = await service.create_plan(name="Plan", workflow_id="wf1")
        with pytest.raises(CompensationRollbackError):
            await service.rollback_plan(plan.id)

    async def test_get_transaction(
        self, service: CompensationService, sample_step: CompensationStep
    ) -> None:
        plan = await service.create_plan(
            name="Plan",
            workflow_id="wf1",
            steps=(sample_step,),
        )
        await service.execute_plan(plan.id)
        # At least one transaction should exist
        assert len(service.transactions) >= 1

    async def test_get_transaction_not_found(self, service: CompensationService) -> None:
        with pytest.raises(CompensationPlanNotFoundError):
            await service.get_transaction("nonexistent")

    async def test_plans_property(self, service: CompensationService) -> None:
        await service.create_plan(name="Plan 1", workflow_id="wf1")
        assert len(service.plans) == 1

    async def test_config_property(self, service: CompensationService) -> None:
        assert service.config.default_strategy == CompensationStrategy.SEQUENTIAL

    async def test_execute_plan_fail_fast(self, service: CompensationService) -> None:
        failing_action = CompensationAction(step_id="s1", action_type="fail_me")
        s1 = CompensationStep(id="s1", name="Failing Step", actions=(failing_action,))
        s2 = CompensationStep(id="s2", name="Should Skip", actions=())
        plan = await service.create_plan(
            name="Fail Fast Plan",
            workflow_id="wf1",
            steps=(s1, s2),
            strategy=CompensationStrategy.FAIL_FAST,
        )
        with pytest.raises(CompensationExecutionError):
            await service.execute_plan(plan.id)
        retrieved = await service.get_plan(plan.id)
        assert retrieved.status == CompensationStatus.FAILED
