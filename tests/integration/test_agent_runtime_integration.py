"""Integration tests for Agent Runtime with real adapters."""

from __future__ import annotations

import pytest

from eaip.adapters.llm.models import LLMResponse
from eaip.agents.models import AgentSpec, Goal, Plan, RunStatus, Step, StepStatus, StepType
from eaip.agents.planner import FixedPlanner, SimpleLLMPlanner
from eaip.agents.runtime import AgentRuntime
from eaip.health.checks import HealthReport, HealthStatus
from eaip.tools.registry import ToolRegistry


class _WeatherTool:
    name = "get_weather"
    description = "Get weather for a city"

    @property
    def parameters(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        }

    async def execute(self, **kwargs: object) -> str:
        return f"Sunny, 25°C in {kwargs.get('city', 'unknown')}"


class _CalculatorTool:
    name = "calculate"
    description = "Perform arithmetic"

    @property
    def parameters(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
        }

    async def execute(self, **kwargs: object) -> str:
        return f"Result: {kwargs.get('expression', '')}"


class _MockLLMAdapter:
    name = "mock"
    version = "0.1.0"

    async def complete(self, request: object, *, context: object | None = None) -> object:
        return LLMResponse(
            model="mock",
            provider="mock",
            content="Mock response for planning",
            finish_reason="stop",
        )

    async def health(self) -> object:
        return HealthReport(component="mock", status=HealthStatus.HEALTHY)


@pytest.fixture
def tool_registry() -> ToolRegistry:
    r = ToolRegistry()
    r.register(_WeatherTool())
    r.register(_CalculatorTool())
    return r


@pytest.fixture
def runtime(tool_registry: ToolRegistry) -> AgentRuntime:
    return AgentRuntime(
        llm_adapter=_MockLLMAdapter(),
        tool_registry=tool_registry,
    )


@pytest.fixture
def agent_spec() -> AgentSpec:
    return AgentSpec(id="weather_bot", name="WeatherBot", tools=("get_weather", "calculate"))


class TestAgentRuntimeWithFixedPlan:
    async def test_execute_weather_tool(self, runtime: AgentRuntime, agent_spec: AgentSpec) -> None:
        goal = Goal(text="Get weather for Paris")
        run = await runtime.create_run(agent_spec, goal)

        plan = Plan(
            goal=goal,
            steps=(
                Step(
                    id="s1",
                    name="get_paris_weather",
                    type=StepType.TOOL_CALL,
                    tool_name="get_weather",
                    input={"city": "Paris"},
                ),
            ),
        )
        runtime._planner = FixedPlanner(plan)

        result = await runtime.start_run(run.id)

        assert result.status is RunStatus.COMPLETED
        assert len(result.steps) == 1
        assert result.steps[0].status is StepStatus.COMPLETED
        assert "Paris" in result.steps[0].output
        assert "Sunny" in result.steps[0].output

    async def test_execute_multi_step_plan(
        self, runtime: AgentRuntime, agent_spec: AgentSpec
    ) -> None:
        goal = Goal(text="Get weather and calculate")
        run = await runtime.create_run(agent_spec, goal)

        plan = Plan(
            goal=goal,
            steps=(
                Step(
                    id="s1",
                    name="weather_step",
                    type=StepType.TOOL_CALL,
                    tool_name="get_weather",
                    input={"city": "Tokyo"},
                ),
                Step(
                    id="s2",
                    name="calc_step",
                    type=StepType.TOOL_CALL,
                    tool_name="calculate",
                    input={"expression": "2 + 2"},
                ),
            ),
        )
        runtime._planner = FixedPlanner(plan)

        result = await runtime.start_run(run.id)

        assert result.status is RunStatus.COMPLETED
        assert len(result.steps) == 2
        assert result.steps[0].status is StepStatus.COMPLETED
        assert result.steps[1].status is StepStatus.COMPLETED
        assert "Tokyo" in result.steps[0].output
        assert "Result" in result.steps[1].output

    async def test_step_failure_does_not_cascade(
        self, runtime: AgentRuntime, agent_spec: AgentSpec
    ) -> None:
        goal = Goal(text="Test partial failure")
        run = await runtime.create_run(agent_spec, goal)

        plan = Plan(
            goal=goal,
            steps=(
                Step(
                    id="s1",
                    name="good_step",
                    type=StepType.TOOL_CALL,
                    tool_name="get_weather",
                    input={"city": "Berlin"},
                ),
                Step(
                    id="s2",
                    name="bad_step",
                    type=StepType.TOOL_CALL,
                    tool_name="nonexistent_tool",
                    input={},
                ),
            ),
        )
        runtime._planner = FixedPlanner(plan)

        result = await runtime.start_run(run.id)

        assert result.status is RunStatus.COMPLETED
        assert result.steps[0].status is StepStatus.COMPLETED
        assert result.steps[1].status is StepStatus.FAILED

    async def test_multiple_runs_independent(
        self, runtime: AgentRuntime, agent_spec: AgentSpec
    ) -> None:
        goal1 = Goal(text="First run")
        goal2 = Goal(text="Second run")

        run1 = await runtime.create_run(agent_spec, goal1)
        run2 = await runtime.create_run(agent_spec, goal2)

        plan = Plan(
            goal=goal1,
            steps=(
                Step(
                    id="s1",
                    name="weather",
                    type=StepType.TOOL_CALL,
                    tool_name="get_weather",
                    input={"city": "London"},
                ),
            ),
        )
        runtime._planner = FixedPlanner(plan)

        result1 = await runtime.start_run(run1.id)
        result2 = await runtime.start_run(run2.id)

        assert result1.id != result2.id
        assert result1.status is RunStatus.COMPLETED
        assert result2.status is RunStatus.COMPLETED


class TestAgentRuntimeWithLLMPlanner:
    async def test_create_plan_via_llm(self, runtime: AgentRuntime, agent_spec: AgentSpec) -> None:
        goal = Goal(text="Get the weather for Tokyo and then calculate 15 + 27")
        run = await runtime.create_run(agent_spec, goal)

        runtime._planner = SimpleLLMPlanner(max_steps=3)
        result = await runtime.start_run(run.id)

        assert result.status in (RunStatus.COMPLETED, RunStatus.FAILED)
        if result.status is RunStatus.COMPLETED:
            assert len(result.steps) >= 1
            assert result.plan is not None

    async def test_persistence_across_runs(
        self, runtime: AgentRuntime, agent_spec: AgentSpec
    ) -> None:
        goal1 = Goal(text="Run one")
        goal2 = Goal(text="Run two")

        run1 = await runtime.create_run(agent_spec, goal1)
        run2 = await runtime.create_run(agent_spec, goal2)

        runs = runtime.list_runs()
        assert len(runs) == 2

        assert runtime.get_run(run1.id) is not None
        assert runtime.get_run(run2.id) is not None
