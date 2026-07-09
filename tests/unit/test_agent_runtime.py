"""Tests for the AgentRuntime orchestrator."""

from __future__ import annotations

import pytest

from eaip.adapters.llm.models import LLMRequest, LLMResponse, RunContext as LLMRunContext
from eaip.agents.base import GuardrailResult
from eaip.agents.exceptions import RunNotFoundError
from eaip.agents.models import AgentSpec, Goal, Plan, RunStatus, Step, StepStatus, StepType
from eaip.agents.planner import FixedPlanner
from eaip.agents.runtime import AgentRunContext, AgentRuntime
from eaip.health.checks import HealthReport, HealthStatus
from eaip.tools.registry import ToolRegistry


class _EchoTool:
    name = "echo"
    description = "Echo back input"

    @property
    def parameters(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        }

    async def execute(self, **kwargs: object) -> str:
        return str(kwargs.get("message", ""))


class _MockLLMAdapter:
    name = "mock"
    version = "0.1.0"

    def __init__(self) -> None:
        self.call_count = 0

    async def complete(
        self, request: LLMRequest, *, context: LLMRunContext | None = None
    ) -> LLMResponse:
        self.call_count += 1
        return LLMResponse(
            model="mock",
            provider="mock",
            content="Mock response",
            finish_reason="stop",
        )

    async def health(self) -> object:
        return HealthReport(component="mock", status=HealthStatus.HEALTHY)


@pytest.fixture
def tool_registry() -> ToolRegistry:
    r = ToolRegistry()
    r.register(_EchoTool())
    return r


@pytest.fixture
def mock_adapter() -> _MockLLMAdapter:
    return _MockLLMAdapter()


@pytest.fixture
def runtime(mock_adapter: _MockLLMAdapter, tool_registry: ToolRegistry) -> AgentRuntime:
    return AgentRuntime(
        llm_adapter=mock_adapter,
        tool_registry=tool_registry,
    )


@pytest.fixture
def agent_spec() -> AgentSpec:
    return AgentSpec(id="agent_1", name="TestAgent", tools=("echo",))


@pytest.fixture
def simple_goal() -> Goal:
    return Goal(text="Say hello")


class TestAgentRuntimeCreate:
    async def test_create_run(
        self, runtime: AgentRuntime, agent_spec: AgentSpec, simple_goal: Goal
    ) -> None:
        run = await runtime.create_run(agent_spec, simple_goal)
        assert run.status is RunStatus.PENDING
        assert run.agent_id == "agent_1"
        assert run.goal.text == "Say hello"

    async def test_create_run_stores_in_registry(
        self, runtime: AgentRuntime, agent_spec: AgentSpec, simple_goal: Goal
    ) -> None:
        run = await runtime.create_run(agent_spec, simple_goal)
        assert runtime.get_run(run.id) is not None

    async def test_list_runs(
        self, runtime: AgentRuntime, agent_spec: AgentSpec, simple_goal: Goal
    ) -> None:
        await runtime.create_run(agent_spec, simple_goal)
        await runtime.create_run(agent_spec, simple_goal)
        runs = runtime.list_runs()
        assert len(runs) == 2

    async def test_list_runs_filter_by_agent(
        self, runtime: AgentRuntime, agent_spec: AgentSpec, simple_goal: Goal
    ) -> None:
        await runtime.create_run(agent_spec, simple_goal)
        spec2 = AgentSpec(id="agent_2", name="Other")
        await runtime.create_run(spec2, simple_goal)
        runs = runtime.list_runs(agent_id="agent_1")
        assert len(runs) == 1
        assert runs[0].agent_id == "agent_1"

    async def test_get_run_not_found(self, runtime: AgentRuntime) -> None:
        assert runtime.get_run("nonexistent") is None

    async def test_create_run_id_is_unique(
        self, runtime: AgentRuntime, agent_spec: AgentSpec, simple_goal: Goal
    ) -> None:
        r1 = await runtime.create_run(agent_spec, simple_goal)
        r2 = await runtime.create_run(agent_spec, simple_goal)
        assert r1.id != r2.id


class TestAgentRuntimeExecute:
    async def test_execute_run_with_fixed_plan(
        self, runtime: AgentRuntime, agent_spec: AgentSpec
    ) -> None:
        goal = Goal(text="Echo hello")
        run = await runtime.create_run(agent_spec, goal)

        plan = Plan(
            goal=goal,
            steps=(
                Step(
                    id="s1",
                    name="echo_hello",
                    type=StepType.TOOL_CALL,
                    tool_name="echo",
                    input={"message": "hello"},
                ),
            ),
        )
        runtime._planner = FixedPlanner(plan)

        result = await runtime.start_run(run.id)

        assert result.status is RunStatus.COMPLETED
        assert len(result.steps) == 1
        assert result.steps[0].status is StepStatus.COMPLETED
        assert "hello" in result.steps[0].output or result.steps[0].output != ""

    async def test_execute_run_calls_planner(
        self, runtime: AgentRuntime, agent_spec: AgentSpec
    ) -> None:
        goal = Goal(text="Do something")
        run = await runtime.create_run(agent_spec, goal)

        plan = Plan(goal=goal, steps=())
        runtime._planner = FixedPlanner(plan)

        result = await runtime.start_run(run.id)
        assert result.plan is not None
        assert result.plan.goal.text == "Do something"

    async def test_execute_run_llm_step(
        self, runtime: AgentRuntime, mock_adapter: _MockLLMAdapter, agent_spec: AgentSpec
    ) -> None:
        goal = Goal(text="Summarize")
        run = await runtime.create_run(agent_spec, goal)

        plan = Plan(
            goal=goal,
            steps=(
                Step(
                    id="s1",
                    name="llm_summarize",
                    type=StepType.LLM_COMPLETION,
                    prompt="Please summarize",
                ),
            ),
        )
        runtime._planner = FixedPlanner(plan)

        result = await runtime.start_run(run.id)

        assert result.status is RunStatus.COMPLETED
        assert len(result.steps) == 1
        assert result.steps[0].status is StepStatus.COMPLETED
        assert result.steps[0].output == "Mock response"

    async def test_run_not_found(self, runtime: AgentRuntime) -> None:
        with pytest.raises(RunNotFoundError):
            await runtime.start_run("nonexistent")

    async def test_run_fails_on_planner_error(
        self, runtime: AgentRuntime, agent_spec: AgentSpec
    ) -> None:
        goal = Goal(text="Fail")
        run = await runtime.create_run(agent_spec, goal)

        class _FailingPlanner:
            name = "fail"

            async def create_plan(self, goal: Goal, context: object) -> Plan:
                msg = "planning error"
                raise RuntimeError(msg)

        runtime._planner = _FailingPlanner()

        result = await runtime.start_run(run.id)
        assert result.status is RunStatus.FAILED
        assert result.error is not None
        assert "planning" in result.error.lower() or "fail" in result.error.lower()

    async def test_run_fails_on_tool_execution_error(
        self, runtime: AgentRuntime, agent_spec: AgentSpec
    ) -> None:
        goal = Goal(text="Cause error")
        await runtime.create_run(agent_spec, goal)

        registry = ToolRegistry()

        class _FailingTool:
            name = "fail_tool"
            description = "Always fails"

            @property
            def parameters(self) -> dict[str, object]:
                return {"type": "object", "properties": {}, "required": []}

            async def execute(self, **kwargs: object) -> str:
                raise RuntimeError("tool failed")

        registry.register(_FailingTool())

        failing_runtime = AgentRuntime(
            llm_adapter=runtime._context.llm_adapter,
            tool_registry=registry,
        )
        failing_run = await failing_runtime.create_run(agent_spec, goal)

        plan = Plan(
            goal=goal,
            steps=(
                Step(id="s1", name="fail_step", type=StepType.TOOL_CALL, tool_name="fail_tool"),
            ),
        )
        failing_runtime._planner = FixedPlanner(plan)

        result = await failing_runtime.start_run(failing_run.id)
        assert result.status is RunStatus.FAILED  # All steps failed => run fails
        assert len(result.steps) == 1
        assert result.steps[0].status is StepStatus.FAILED


class TestAgentRuntimeCancel:
    async def test_cancel_pending_run(
        self, runtime: AgentRuntime, agent_spec: AgentSpec, simple_goal: Goal
    ) -> None:
        run = await runtime.create_run(agent_spec, simple_goal)
        cancelled = await runtime.cancel_run(run.id)
        assert cancelled is not None
        assert cancelled.status is RunStatus.CANCELLED

    async def test_cancel_nonexistent_run(self, runtime: AgentRuntime) -> None:
        result = await runtime.cancel_run("nonexistent")
        assert result is None

    async def test_cancel_completed_run(self, runtime: AgentRuntime, agent_spec: AgentSpec) -> None:
        goal = Goal(text="Quick")
        run = await runtime.create_run(agent_spec, goal)
        plan = Plan(goal=goal, steps=())
        runtime._planner = FixedPlanner(plan)
        await runtime.start_run(run.id)

        cancelled = await runtime.cancel_run(run.id)
        assert cancelled is not None
        assert cancelled.status is RunStatus.COMPLETED  # Already completed


class TestAgentRunContext:
    async def test_context_properties(
        self, mock_adapter: _MockLLMAdapter, tool_registry: ToolRegistry
    ) -> None:
        ctx = AgentRunContext(
            llm_adapter=mock_adapter,
            tool_registry=tool_registry,
        )
        assert ctx.llm_adapter is mock_adapter
        assert ctx.tool_registry is tool_registry
        assert ctx.memory is None
        assert ctx.event_bus is None
        assert ctx.meter is None

    async def test_to_run_context(
        self, mock_adapter: _MockLLMAdapter, tool_registry: ToolRegistry
    ) -> None:
        ctx = AgentRunContext(llm_adapter=mock_adapter, tool_registry=tool_registry)
        rc = ctx.to_run_context()
        assert rc.tenant_id == ""
        assert isinstance(rc, LLMRunContext)


class TestAgentRuntimeHealth:
    async def test_health_healthy(self, runtime: AgentRuntime) -> None:
        report = await runtime.health()
        assert report.status is HealthStatus.HEALTHY
        assert report.component == "agent_runtime"
        assert "total runs" in report.message.lower()


class TestAgentRuntimeGuardrail:
    async def test_guardrail_blocks_step(
        self, runtime: AgentRuntime, agent_spec: AgentSpec
    ) -> None:
        goal = Goal(text="Blocked")
        run = await runtime.create_run(agent_spec, goal)

        plan = Plan(
            goal=goal,
            steps=(
                Step(
                    id="s1",
                    name="blocked_step",
                    type=StepType.TOOL_CALL,
                    tool_name="echo",
                    input={"message": "hi"},
                ),
            ),
        )
        runtime._planner = FixedPlanner(plan)

        Step(id="s1", name="blocked_step", type=StepType.TOOL_CALL)

        class _BlockingGuardrail:
            name = "blocker"

            async def before_step(self, step: Step, context: object) -> object:
                return GuardrailResult(blocked=True, reason="blocked by test")

            async def after_step(self, step: Step, context: object) -> object:
                return GuardrailResult()

        runtime._guardrail = _BlockingGuardrail()

        result = await runtime.start_run(run.id)
        assert result.status is RunStatus.COMPLETED
        assert len(result.steps) == 1
        assert result.steps[0].status is StepStatus.SKIPPED
        assert "blocked" in (result.steps[0].error or "")
