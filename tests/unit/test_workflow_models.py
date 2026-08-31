"""Tests for Workflow domain models."""

from __future__ import annotations

from datetime import datetime

import pytest

from eaip.shared.time import utc_now
from eaip.workflow.models import (
    DurableExecutionConfig,
    EdgeCondition,
    ParallelGroup,
    ParentChildConfig,
    RetryPolicy,
    TimeoutConfig,
    WorkflowContext,
    WorkflowDefinition,
    WorkflowEdge,
    WorkflowResult,
    WorkflowRun,
    WorkflowStatus,
    WorkflowStep,
    WorkflowStepRecord,
    WorkflowStepStatus,
)


class TestWorkflowStatus:
    def test_values(self) -> None:
        assert WorkflowStatus.PENDING == "pending"
        assert WorkflowStatus.RUNNING == "running"
        assert WorkflowStatus.PAUSED == "paused"
        assert WorkflowStatus.COMPLETED == "completed"
        assert WorkflowStatus.FAILED == "failed"
        assert WorkflowStatus.CANCELLED == "cancelled"
        assert WorkflowStatus.TIMED_OUT == "timed_out"

    def test_valid_members(self) -> None:
        assert len(WorkflowStatus) == 8


class TestWorkflowStepStatus:
    def test_values(self) -> None:
        assert WorkflowStepStatus.PENDING == "pending"
        assert WorkflowStepStatus.WAITING_APPROVAL == "waiting_approval"
        assert WorkflowStepStatus.APPROVED == "approved"
        assert WorkflowStepStatus.REJECTED == "rejected"

    def test_valid_members(self) -> None:
        assert len(WorkflowStepStatus) == 10


class TestEdgeCondition:
    def test_values(self) -> None:
        assert EdgeCondition.ALWAYS == "always"
        assert EdgeCondition.ON_SUCCESS == "on_success"
        assert EdgeCondition.ON_FAILURE == "on_failure"
        assert EdgeCondition.EXPRESSION == "expression"


class TestWorkflowEdge:
    def test_defaults(self) -> None:
        e = WorkflowEdge(source_id="s1", target_id="s2")
        assert e.source_id == "s1"
        assert e.target_id == "s2"
        assert e.condition is EdgeCondition.ALWAYS
        assert e.expression == ""
        assert e.label == ""

    def test_frozen(self) -> None:
        e = WorkflowEdge(source_id="a", target_id="b")
        with pytest.raises(ValueError):
            e.source_id = "c"  # type: ignore[misc]


class TestRetryPolicy:
    def test_defaults(self) -> None:
        r = RetryPolicy()
        assert r.max_attempts == 3
        assert r.delay_seconds == 1.0
        assert r.backoff_multiplier == 2.0
        assert r.max_delay_seconds == 60.0
        assert r.jitter == 0.0

    def test_custom(self) -> None:
        r = RetryPolicy(max_attempts=5, delay_seconds=2.0, jitter=0.1)
        assert r.max_attempts == 5
        assert r.delay_seconds == 2.0
        assert r.jitter == 0.1

    def test_frozen(self) -> None:
        r = RetryPolicy()
        with pytest.raises(ValueError):
            r.max_attempts = 5  # type: ignore[misc]


class TestWorkflowStep:
    def test_required_fields(self) -> None:
        s = WorkflowStep(id="s1", name="Step One")
        assert s.id == "s1"
        assert s.name == "Step One"
        assert s.agent_id == ""
        assert s.tool_name == ""
        assert s.prompt == ""
        assert s.input == {}
        assert s.timeout_seconds == 0.0
        assert s.retry_policy is None

    def test_with_agent(self) -> None:
        s = WorkflowStep(
            id="s1",
            name="Analyze",
            agent_id="agent_1",
            prompt="Analyze the data",
            timeout_seconds=30.0,
        )
        assert s.agent_id == "agent_1"
        assert s.prompt == "Analyze the data"
        assert s.timeout_seconds == 30.0

    def test_with_tool(self) -> None:
        s = WorkflowStep(
            id="s1",
            name="Call API",
            tool_name="weather",
            input={"location": "NYC"},
        )
        assert s.tool_name == "weather"
        assert s.input == {"location": "NYC"}

    def test_with_retry(self) -> None:
        rp = RetryPolicy(max_attempts=5)
        s = WorkflowStep(id="s1", name="Retryable", retry_policy=rp)
        assert s.retry_policy is not None
        assert s.retry_policy.max_attempts == 5

    def test_with_approval(self) -> None:
        s = WorkflowStep(
            id="s1",
            name="Approval Step",
            requires_approval=True,
            approval_prompt="Please approve",
        )
        assert s.requires_approval is True
        assert s.approval_prompt == "Please approve"

    def test_frozen(self) -> None:
        s = WorkflowStep(id="s1", name="Test")
        with pytest.raises(ValueError):
            s.name = "changed"  # type: ignore[misc]


class TestWorkflowDefinition:
    def test_required_fields(self) -> None:
        d = WorkflowDefinition(id="wf_1", name="My Workflow")
        assert d.id == "wf_1"
        assert d.name == "My Workflow"
        assert d.description == ""
        assert d.version == "0.1.0"
        assert d.steps == ()
        assert d.edges == ()
        assert d.entry_point == ""

    def test_with_steps_and_edges(self) -> None:
        steps = (
            WorkflowStep(id="s1", name="Step 1"),
            WorkflowStep(id="s2", name="Step 2"),
        )
        edges = (WorkflowEdge(source_id="s1", target_id="s2"),)
        d = WorkflowDefinition(
            id="wf_1",
            name="Two Step",
            steps=steps,
            edges=edges,
            entry_point="s1",
        )
        assert len(d.steps) == 2
        assert len(d.edges) == 1
        assert d.entry_point == "s1"

    def test_with_new_configs(self) -> None:
        d = WorkflowDefinition(
            id="wf_cfg",
            name="With Configs",
            timeout_config=TimeoutConfig(workflow_timeout_seconds=30.0),
            durable_config=DurableExecutionConfig(enabled=True),
            parent_child_config=ParentChildConfig(propagate_failure=False),
            parallel_groups=(ParallelGroup(id="g1", step_ids=("s1", "s2")),),
        )
        assert d.timeout_config is not None
        assert d.timeout_config.workflow_timeout_seconds == 30.0
        assert d.durable_config is not None
        assert d.durable_config.enabled is True
        assert d.parent_child_config is not None
        assert d.parent_child_config.propagate_failure is False
        assert len(d.parallel_groups) == 1


class TestWorkflowStepRecord:
    def test_defaults(self) -> None:
        r = WorkflowStepRecord(step_id="s1", name="Test")
        assert r.status is WorkflowStepStatus.PENDING
        assert r.attempt == 0
        assert r.duration_ms == 0.0
        assert r.error is None
        assert r.started_at is None
        assert r.completed_at is None

    def test_completed(self) -> None:
        now = utc_now()
        r = WorkflowStepRecord(
            step_id="s1",
            name="Done",
            status=WorkflowStepStatus.COMPLETED,
            output="success",
            duration_ms=150.0,
            started_at=now,
        )
        assert r.output == "success"
        assert r.duration_ms == 150.0
        assert r.started_at == now

    def test_frozen(self) -> None:
        r = WorkflowStepRecord(step_id="s1", name="T")
        with pytest.raises(ValueError):
            r.status = WorkflowStepStatus.COMPLETED  # type: ignore[misc]

    def test_with_approval_token(self) -> None:
        r = WorkflowStepRecord(
            step_id="s1",
            name="Approval",
            status=WorkflowStepStatus.WAITING_APPROVAL,
            approval_token="tok_123",
        )
        assert r.approval_token == "tok_123"
        assert r.status is WorkflowStepStatus.WAITING_APPROVAL


class TestWorkflowRun:
    def test_defaults(self) -> None:
        d = WorkflowDefinition(id="wf_1", name="WF")
        r = WorkflowRun(id="run_1", workflow_id="wf_1", definition=d)
        assert r.status is WorkflowStatus.PENDING
        assert r.steps == ()
        assert r.context == {}
        assert r.result == ""
        assert r.error is None
        assert r.resume_token is None
        assert r.parent_run_id is None
        assert isinstance(r.created_at, datetime)

    def test_with_fields(self) -> None:
        d = WorkflowDefinition(id="wf_1", name="WF")
        r = WorkflowRun(
            id="run_1",
            workflow_id="wf_1",
            definition=d,
            status=WorkflowStatus.COMPLETED,
            result="done",
            context={"key": "val"},
            parent_run_id="parent_1",
        )
        assert r.status is WorkflowStatus.COMPLETED
        assert r.result == "done"
        assert r.context == {"key": "val"}
        assert r.parent_run_id == "parent_1"

    def test_with_child_runs(self) -> None:
        d = WorkflowDefinition(id="wf_1", name="WF")
        r = WorkflowRun(
            id="r1",
            workflow_id="wf_1",
            definition=d,
            child_run_ids=("child1", "child2"),
            state_machine_state="running",
        )
        assert r.child_run_ids == ("child1", "child2")
        assert r.state_machine_state == "running"

    def test_frozen(self) -> None:
        d = WorkflowDefinition(id="wf_1", name="WF")
        r = WorkflowRun(id="r1", workflow_id="wf_1", definition=d)
        with pytest.raises(ValueError):
            r.status = WorkflowStatus.RUNNING  # type: ignore[misc]


class TestWorkflowResult:
    def test_defaults(self) -> None:
        res = WorkflowResult(run_id="r1", workflow_id="wf_1", status=WorkflowStatus.COMPLETED)
        assert res.result == ""
        assert res.error is None
        assert res.step_count == 0
        assert res.duration_ms == 0.0
        assert res.timed_out_count == 0
        assert res.child_results == ()

    def test_failed(self) -> None:
        res = WorkflowResult(
            run_id="r1",
            workflow_id="wf_1",
            status=WorkflowStatus.FAILED,
            error="something broke",
            failed_count=1,
            duration_ms=500.0,
        )
        assert res.error == "something broke"
        assert res.failed_count == 1
        assert res.duration_ms == 500.0

    def test_timed_out(self) -> None:
        res = WorkflowResult(
            run_id="r1",
            workflow_id="wf_1",
            status=WorkflowStatus.TIMED_OUT,
            timed_out_count=2,
        )
        assert res.status is WorkflowStatus.TIMED_OUT
        assert res.timed_out_count == 2


class TestTimeoutConfig:
    def test_defaults(self) -> None:
        tc = TimeoutConfig()
        assert tc.workflow_timeout_seconds == 0.0
        assert tc.step_timeout_seconds == 0.0
        assert tc.approval_timeout_seconds == 3600.0


class TestDurableExecutionConfig:
    def test_defaults(self) -> None:
        dc = DurableExecutionConfig()
        assert dc.enabled is False
        assert dc.store_type == "memory"
        assert dc.persist_after_each_step is True


class TestParentChildConfig:
    def test_defaults(self) -> None:
        pc = ParentChildConfig()
        assert pc.propagate_failure is True
        assert pc.inherit_context is True
        assert pc.wait_for_completion is True


class TestParallelGroup:
    def test_defaults(self) -> None:
        pg = ParallelGroup(id="g1", step_ids=("s1", "s2"))
        assert pg.id == "g1"
        assert pg.step_ids == ("s1", "s2")
        assert pg.completion_condition == "all"
        assert pg.required_count == 0

    def test_frozen(self) -> None:
        pg = ParallelGroup(id="g1", step_ids=("s1",))
        with pytest.raises(ValueError):
            pg.id = "g2"  # type: ignore[misc]


class TestWorkflowContext:
    def test_defaults(self) -> None:
        ctx = WorkflowContext()
        assert ctx.variables == {}
        assert ctx.agent_outputs == {}
        assert ctx.shared_memory_keys == ()

    def test_get_and_set(self) -> None:
        ctx = WorkflowContext()
        assert ctx.get("missing", "default") == "default"
        ctx2 = ctx.set("key1", "value1")
        assert ctx2.get("key1") == "value1"
        assert ctx.get("key1", "default") == "default"  # immutable

    def test_immutable_on_set(self) -> None:
        ctx = WorkflowContext()
        ctx2 = ctx.set("a", "1")
        assert ctx is not ctx2
        assert ctx.variables == {}
        assert ctx2.variables == {"a": "1"}

    def test_add_agent_output(self) -> None:
        ctx = WorkflowContext()
        ctx2 = ctx.add_agent_output("step1", "result1")
        assert ctx2.agent_outputs == {"step1": "result1"}
        assert ctx.agent_outputs == {}

    def test_add_tool_output(self) -> None:
        ctx = WorkflowContext()
        ctx2 = ctx.add_tool_output("step1", "tool_result")
        assert ctx2.tool_outputs == {"step1": "tool_result"}

    def test_add_memory_key(self) -> None:
        ctx = WorkflowContext()
        ctx2 = ctx.add_memory_key("mem1")
        assert "mem1" in ctx2.shared_memory_keys
        ctx3 = ctx2.add_memory_key("mem1")  # dedup
        assert len(ctx3.shared_memory_keys) == 1
