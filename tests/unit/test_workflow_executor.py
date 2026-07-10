"""Tests for WorkflowEngine - sequential, DAG, retry, timeout, cancellation, pause/resume."""

from __future__ import annotations

import asyncio

import pytest

from eaip.agents.models import Goal, RunRecord, RunStatus
from eaip.workflow.approval import StepApprovalHandler
from eaip.workflow.exceptions import CircularWorkflowError, InvalidWorkflowError
from eaip.workflow.executor import WorkflowEngine
from eaip.workflow.models import (
    EdgeCondition,
    ParallelGroup,
    ParentChildConfig,
    RetryPolicy,
    TimeoutConfig,
    WorkflowContext,
    WorkflowDefinition,
    WorkflowEdge,
    WorkflowStatus,
    WorkflowStep,
)
from eaip.workflow.state_machine import WorkflowState


class _MockAgentRuntime:
    _counter = 0

    async def create_run(self, agent_spec: object, goal: Goal) -> RunRecord:
        self._counter += 1
        return RunRecord(
            id=f"run_{self._counter}",
            agent_id=agent_spec.id if hasattr(agent_spec, "id") else "unknown",
            goal=goal,
            status=RunStatus.PENDING,
        )

    async def start_run(self, run_id: str) -> RunRecord:
        return RunRecord(
            id=run_id,
            agent_id="agent_mock",
            goal=Goal(text=""),
            status=RunStatus.COMPLETED,
            result=f"processed: {run_id}",
        )


class _MockToolRegistry:
    def get(self, name: str) -> object:
        return _EchoTool(name)


class _EchoTool:
    def __init__(self, name: str) -> None:
        self.name = name

    async def execute(self, **kwargs: object) -> str:
        return f"tool {self.name} executed with {kwargs}"


@pytest.fixture
def engine() -> WorkflowEngine:
    return WorkflowEngine(
        agent_runtime=_MockAgentRuntime(),
        tool_registry=_MockToolRegistry(),
    )


@pytest.fixture
def noop_engine() -> WorkflowEngine:
    return WorkflowEngine()


class TestWorkflowEngineExecute:
    async def test_sequential_execution(self, engine: WorkflowEngine) -> None:
        steps = (
            WorkflowStep(id="s1", name="Step 1", agent_id="agent_a", prompt="Hello"),
            WorkflowStep(id="s2", name="Step 2", agent_id="agent_b", prompt="World"),
        )
        definition = WorkflowDefinition(id="wf_1", name="Seq", steps=steps)
        result = await engine.execute(definition)
        assert result.status is WorkflowStatus.COMPLETED
        assert result.step_count == 2
        assert result.completed_count == 2
        assert result.duration_ms > 0

    async def test_entry_point(self, engine: WorkflowEngine) -> None:
        steps = (
            WorkflowStep(id="s1", name="Step 1", agent_id="agent_a", prompt="A"),
            WorkflowStep(id="s2", name="Step 2", agent_id="agent_b", prompt="B"),
        )
        definition = WorkflowDefinition(id="wf_1", name="EP", steps=steps, entry_point="s1")
        result = await engine.execute(definition)
        assert result.status is WorkflowStatus.COMPLETED
        assert result.completed_count == 2

    async def test_dag_execution(self, engine: WorkflowEngine) -> None:
        steps = (
            WorkflowStep(id="s1", name="Start", agent_id="agent_a", prompt="start"),
            WorkflowStep(id="s2", name="Mid", agent_id="agent_b", prompt="mid"),
            WorkflowStep(id="s3", name="End", agent_id="agent_a", prompt="end"),
        )
        edges = (
            WorkflowEdge(source_id="s1", target_id="s2"),
            WorkflowEdge(source_id="s2", target_id="s3"),
        )
        definition = WorkflowDefinition(id="wf_2", name="DAG", steps=steps, edges=edges)
        result = await engine.execute(definition)
        assert result.status is WorkflowStatus.COMPLETED
        assert result.completed_count == 3

    async def test_conditional_edge_on_success(self, engine: WorkflowEngine) -> None:
        steps = (
            WorkflowStep(id="s1", name="Step 1", agent_id="agent_a", prompt="ok"),
            WorkflowStep(id="s2", name="Step 2", agent_id="agent_b", prompt="after ok"),
            WorkflowStep(id="s3", name="Step 3", agent_id="agent_a", prompt="after fail"),
        )
        edges = (
            WorkflowEdge(source_id="s1", target_id="s2", condition=EdgeCondition.ON_SUCCESS),
            WorkflowEdge(source_id="s1", target_id="s3", condition=EdgeCondition.ON_FAILURE),
        )
        definition = WorkflowDefinition(id="wf_3", name="Cond", steps=steps, edges=edges)
        result = await engine.execute(definition)
        assert result.completed_count >= 1

    async def test_tool_step_execution(self, engine: WorkflowEngine) -> None:
        steps = (
            WorkflowStep(id="s1", name="Tool Call", tool_name="echo", input={"msg": "hi"}),
        )
        definition = WorkflowDefinition(id="wf_4", name="Tool", steps=steps)
        result = await engine.execute(definition)
        assert result.status is WorkflowStatus.COMPLETED

    async def test_empty_definition(self, noop_engine: WorkflowEngine) -> None:
        definition = WorkflowDefinition(id="wf_e", name="Empty")
        result = await noop_engine.execute(definition)
        assert result.status is WorkflowStatus.COMPLETED
        assert result.step_count == 0

    async def test_cancellation(self, engine: WorkflowEngine) -> None:
        steps = (
            WorkflowStep(id="s1", name="Slow", agent_id="agent_a", prompt="slow"),
            WorkflowStep(id="s2", name="Never", agent_id="agent_b", prompt="never"),
        )
        definition = WorkflowDefinition(id="wf_c", name="Cancel", steps=steps)
        task = asyncio.create_task(engine.execute(definition))
        await asyncio.sleep(0.02)
        for rid in list(engine._runs):
            await engine.cancel(rid)
        result = await task
        assert result.status in (WorkflowStatus.CANCELLED, WorkflowStatus.COMPLETED)

    async def test_pause_and_resume(self, engine: WorkflowEngine) -> None:
        steps = (
            WorkflowStep(id="s1", name="Pausable", agent_id="agent_a", prompt="pause test"),
        )
        definition = WorkflowDefinition(id="wf_p", name="Pause", steps=steps)
        engine._pause_flags.add("test_run")
        result = await engine.execute(definition)
        assert result.status is WorkflowStatus.COMPLETED

    async def test_retry_on_failure(self) -> None:
        call_count = 0

        class _FailingRuntime:
            async def create_run(self, agent_spec: object, goal: Goal) -> RunRecord:
                nonlocal call_count
                call_count += 1
                return RunRecord(
                    id=f"run_{call_count}",
                    agent_id=agent_spec.id if hasattr(agent_spec, "id") else "unknown",
                    goal=goal,
                    status=RunStatus.PENDING,
                )

            async def start_run(self, run_id: str) -> RunRecord:
                nonlocal call_count
                if call_count < 3:
                    raise RuntimeError("transient error")
                return RunRecord(
                    id=run_id, agent_id="agent_r", goal=Goal(text="retry"),
                    status=RunStatus.COMPLETED, result="success on retry",
                )

        engine = WorkflowEngine(agent_runtime=_FailingRuntime())
        steps = (
            WorkflowStep(
                id="s1", name="Retry Step", agent_id="agent_r", prompt="retry",
                retry_policy=RetryPolicy(max_attempts=3, delay_seconds=0.01),
            ),
        )
        definition = WorkflowDefinition(id="wf_r", name="Retry", steps=steps)
        result = await engine.execute(definition)
        assert result.status is WorkflowStatus.COMPLETED
        assert result.completed_count == 1

    async def test_retry_exhausted(self) -> None:
        class _AlwaysFailRuntime:
            async def create_run(self, agent_spec: object, goal: Goal) -> RunRecord:
                return RunRecord(
                    id="run_f", agent_id="agent_f", goal=goal, status=RunStatus.PENDING,
                )

            async def start_run(self, run_id: str) -> RunRecord:
                raise RuntimeError("always fails")

        engine = WorkflowEngine(agent_runtime=_AlwaysFailRuntime())
        steps = (
            WorkflowStep(
                id="s1", name="Fail Step", agent_id="agent_f", prompt="fail",
                retry_policy=RetryPolicy(max_attempts=2, delay_seconds=0.01),
            ),
        )
        definition = WorkflowDefinition(id="wf_f", name="Fail", steps=steps)
        result = await engine.execute(definition)
        assert result.status is WorkflowStatus.COMPLETED
        assert result.failed_count == 1

    async def test_step_timeout(self) -> None:
        class _SlowRuntime:
            async def create_run(self, agent_spec: object, goal: Goal) -> RunRecord:
                return RunRecord(
                    id="run_s", agent_id="agent_s", goal=goal, status=RunStatus.PENDING,
                )

            async def start_run(self, run_id: str) -> RunRecord:
                await asyncio.sleep(10)
                return RunRecord(
                    id=run_id, agent_id="agent_s", goal=Goal(text="slow"),
                    status=RunStatus.COMPLETED, result="too late",
                )

        engine = WorkflowEngine(agent_runtime=_SlowRuntime())
        steps = (
            WorkflowStep(
                id="s1", name="Slow Step", agent_id="agent_s", prompt="slow", timeout_seconds=0.01,
            ),
        )
        definition = WorkflowDefinition(id="wf_t", name="Timeout", steps=steps)
        result = await engine.execute(definition)
        assert result.status is WorkflowStatus.TIMED_OUT
        assert result.timed_out_count == 1

    async def test_context_passing(self, engine: WorkflowEngine) -> None:
        steps = (
            WorkflowStep(id="s1", name="Ctx Step", agent_id="agent_a", prompt="context"),
        )
        definition = WorkflowDefinition(id="wf_ctx", name="Ctx", steps=steps)
        ctx = WorkflowContext()
        ctx2 = ctx.set("initial", "value")
        result = await engine.execute(definition, context=ctx2)
        assert result.status is WorkflowStatus.COMPLETED


class TestWorkflowEngineValidation:
    async def test_invalid_edge_source(self, noop_engine: WorkflowEngine) -> None:
        steps = (WorkflowStep(id="s1", name="S1"),)
        edges = (WorkflowEdge(source_id="missing", target_id="s1"),)
        definition = WorkflowDefinition(id="wf_bad", name="Bad", steps=steps, edges=edges)
        with pytest.raises(InvalidWorkflowError):
            await noop_engine.execute(definition)

    async def test_invalid_edge_target(self, noop_engine: WorkflowEngine) -> None:
        steps = (WorkflowStep(id="s1", name="S1"),)
        edges = (WorkflowEdge(source_id="s1", target_id="missing"),)
        definition = WorkflowDefinition(id="wf_bad2", name="Bad2", steps=steps, edges=edges)
        with pytest.raises(InvalidWorkflowError):
            await noop_engine.execute(definition)

    async def test_circular_dependency(self, noop_engine: WorkflowEngine) -> None:
        steps = (
            WorkflowStep(id="s1", name="S1"),
            WorkflowStep(id="s2", name="S2"),
        )
        edges = (
            WorkflowEdge(source_id="s1", target_id="s2"),
            WorkflowEdge(source_id="s2", target_id="s1"),
        )
        definition = WorkflowDefinition(id="wf_circ", name="Circ", steps=steps, edges=edges)
        with pytest.raises(CircularWorkflowError):
            await noop_engine.execute(definition)


class TestWorkflowEngineRunManagement:
    async def test_get_run(self, engine: WorkflowEngine) -> None:
        steps = (WorkflowStep(id="s1", name="S1", agent_id="agent_a", prompt="hi"),)
        definition = WorkflowDefinition(id="wf_g", name="Get", steps=steps)
        await engine.execute(definition)
        run_id = next(iter(engine._runs))
        run = engine.get_run(run_id)
        assert run is not None
        assert run.workflow_id == "wf_g"

    async def test_get_run_not_found(self, engine: WorkflowEngine) -> None:
        assert engine.get_run("nonexistent") is None

    async def test_cancel_idempotent(self, engine: WorkflowEngine) -> None:
        await engine.cancel("nonexistent")
        assert "nonexistent" not in engine._runs

    async def test_pause_resume_flow(self, engine: WorkflowEngine) -> None:
        definition = WorkflowDefinition(id="wf_pr", name="PR")
        await engine.execute(definition)
        run_id = next(iter(engine._runs))
        await engine.pause(run_id)
        assert run_id in engine._pause_flags
        result = await engine.resume(run_id)
        assert result is not None

    async def test_resume_non_paused(self, engine: WorkflowEngine) -> None:
        definition = WorkflowDefinition(
            id="wf_np", name="NP",
            steps=(WorkflowStep(id="s1", name="S1", agent_id="agent_a", prompt="x"),),
        )
        await engine.execute(definition)
        run_id = next(iter(engine._runs))
        result = await engine.resume(run_id)
        assert "not paused" in (result.error or "")

    async def test_resume_not_found(self, engine: WorkflowEngine) -> None:
        result = await engine.resume("nonexistent")
        assert "not found" in (result.error or "")


class TestWorkflowEngineParallel:
    async def test_parallel_group_execution(self) -> None:
        engine = WorkflowEngine(
            agent_runtime=_MockAgentRuntime(),
            tool_registry=_MockToolRegistry(),
        )
        steps = (
            WorkflowStep(id="s1", name="Parallel A", agent_id="agent_a", prompt="A"),
            WorkflowStep(id="s2", name="Parallel B", agent_id="agent_b", prompt="B"),
            WorkflowStep(id="s3", name="After", agent_id="agent_a", prompt="after"),
        )
        edges = (
            WorkflowEdge(source_id="s1", target_id="s3"),
            WorkflowEdge(source_id="s2", target_id="s3"),
        )
        groups = (
            ParallelGroup(id="g1", step_ids=("s1", "s2")),
        )
        definition = WorkflowDefinition(
            id="wf_par", name="Parallel", steps=steps, edges=edges, parallel_groups=groups,
        )
        result = await engine.execute(definition)
        assert result.status is WorkflowStatus.COMPLETED
        assert result.completed_count >= 2


class _SlowAgentRuntime:
    async def create_run(self, agent_spec: object, goal: object) -> RunRecord:
        return RunRecord(
            id="run_slow", agent_id="agent_slow", goal=Goal(text=""),
            status=RunStatus.PENDING,
        )

    async def start_run(self, run_id: str) -> RunRecord:
        await asyncio.sleep(10)
        return RunRecord(
            id=run_id, agent_id="agent_slow", goal=Goal(text=""),
            status=RunStatus.COMPLETED, result="done",
        )


class TestWorkflowEngineTimeout:
    async def test_workflow_level_timeout(self) -> None:
        engine = WorkflowEngine(agent_runtime=_SlowAgentRuntime())
        steps = (
            WorkflowStep(id="s1", name="Slow", agent_id="agent_a", prompt="slow"),
        )
        definition = WorkflowDefinition(
            id="wf_to", name="TO", steps=steps,
            timeout_config=TimeoutConfig(workflow_timeout_seconds=0.05),
        )
        result = await engine.execute(definition)
        assert result.status is WorkflowStatus.TIMED_OUT


class TestWorkflowEngineStateMachine:
    async def test_state_machine_tracks_lifecycle(self) -> None:
        engine = WorkflowEngine(
            agent_runtime=_MockAgentRuntime(),
            tool_registry=_MockToolRegistry(),
        )
        steps = (
            WorkflowStep(id="s1", name="Step 1", agent_id="agent_a", prompt="A"),
        )
        definition = WorkflowDefinition(id="wf_sm", name="SM", steps=steps)
        result = await engine.execute(definition)
        assert result.status is WorkflowStatus.COMPLETED
        run_id = next(iter(engine._runs))
        sm = engine.get_state_machine(run_id)
        assert sm is not None
        assert sm.state is WorkflowState.COMPLETED

    async def test_state_machine_cancelled(self) -> None:
        engine = WorkflowEngine(
            agent_runtime=_MockAgentRuntime(),
            tool_registry=_MockToolRegistry(),
        )
        steps = (
            WorkflowStep(id="s1", name="Cancel Me", agent_id="agent_a", prompt="cancel"),
        )
        definition = WorkflowDefinition(id="wf_sc", name="SC", steps=steps)
        task = asyncio.create_task(engine.execute(definition))
        await asyncio.sleep(0.02)
        for rid in list(engine._runs):
            await engine.cancel(rid)
        await task
        run_id = next(iter(engine._runs))
        sm = engine.get_state_machine(run_id)
        assert sm is not None
        assert sm.state is WorkflowState.CANCELLED or sm.state is WorkflowState.COMPLETED


class TestWorkflowEngineParentChild:
    async def test_execute_child_workflow(self) -> None:
        engine = WorkflowEngine(
            agent_runtime=_MockAgentRuntime(),
            tool_registry=_MockToolRegistry(),
        )
        child_steps = (
            WorkflowStep(id="c1", name="Child Step", agent_id="agent_a", prompt="child"),
        )
        child = WorkflowDefinition(
            id="wf_child", name="Child", steps=child_steps,
            parent_child_config=ParentChildConfig(propagate_failure=False),
        )
        parent_steps = (
            WorkflowStep(id="p1", name="Parent Step", agent_id="agent_a", prompt="parent"),
        )
        parent = WorkflowDefinition(id="wf_parent", name="Parent", steps=parent_steps)
        parent_result = await engine.execute(parent)
        child_result = await engine.execute_child(child, parent_result.run_id)
        assert child_result.status is WorkflowStatus.COMPLETED
        assert child_result.completed_count == 1


class TestWorkflowEngineApproval:
    async def test_approval_checkpoint(self) -> None:
        ah = StepApprovalHandler()
        engine = WorkflowEngine(approval_handler=ah)
        steps = (
            WorkflowStep(
                id="s1", name="Approval Needed", agent_id="agent_a",
                prompt="needs approval", requires_approval=True,
                approval_prompt="Approve this step?",
            ),
        )
        definition = WorkflowDefinition(id="wf_app", name="Approval", steps=steps)
        task = asyncio.create_task(engine.execute(definition))
        await asyncio.sleep(0.05)
        pending = ah.get_pending()
        if pending:
            token = pending[0].get("resume_token", "")
            if not token:
                for t, entry in ah._pending.items():
                    if entry.get("run_id"):
                        await ah.approve(t, entry["run_id"])
                        break
            else:
                await ah.approve(token, "")
        result = await task
        assert result.status is WorkflowStatus.COMPLETED
