"""Tests for Planner implementations."""

from __future__ import annotations

import pytest

from eaip.adapters.llm.models import LLMRequest, LLMResponse, RunContext as LLMRunContext
from eaip.agents.models import Goal, Plan, Step, StepType
from eaip.agents.planner import FixedPlanner, SimpleLLMPlanner
from eaip.agents.runtime import AgentRunContext
from eaip.health.checks import HealthReport, HealthStatus
from eaip.tools.registry import ToolRegistry


class _MockPlannerAdapter:
    name = "mock"
    version = "0.1.0"

    async def complete(
        self, request: LLMRequest, *, context: LLMRunContext | None = None
    ) -> LLMResponse:
        content = (
            "STEP 1: tool_call | get_weather | get_weather\n"
            "STEP 2: llm_completion | summarize | Summarize the weather data\n"
            "STEP 3: tool_call | send_email | send_email\n"
        )
        return LLMResponse(
            model="mock",
            provider="mock",
            content=content,
            finish_reason="stop",
        )

    async def health(self) -> object:
        return HealthReport(component="mock", status=HealthStatus.HEALTHY)


class _EmptyAdapter:
    name = "mock"
    version = "0.1.0"

    async def complete(
        self, request: LLMRequest, *, context: LLMRunContext | None = None
    ) -> LLMResponse:
        return LLMResponse(
            model="mock", provider="mock", content="No valid steps here", finish_reason="stop"
        )

    async def health(self) -> object:
        return HealthReport(component="mock", status=HealthStatus.HEALTHY)


@pytest.fixture
def tool_registry() -> ToolRegistry:
    return ToolRegistry()


@pytest.fixture
def context(tool_registry: ToolRegistry) -> AgentRunContext:
    return AgentRunContext(
        llm_adapter=_MockPlannerAdapter(),
        tool_registry=tool_registry,
    )


class TestFixedPlanner:
    async def test_returns_predefined_plan(self) -> None:
        goal = Goal(text="test")
        steps = (Step(id="s1", name="step1", type=StepType.TOOL_CALL, tool_name="echo"),)
        expected = Plan(goal=goal, steps=steps, reasoning="fixed")
        planner = FixedPlanner(expected)
        result = await planner.create_plan(goal, object())  # type: ignore[arg-type]
        assert result is expected
        assert len(result.steps) == 1

    async def test_ignores_goal(self) -> None:
        goal = Goal(text="original")
        steps = (Step(id="s1", name="s1", type=StepType.TOOL_CALL, tool_name="echo"),)
        plan = Plan(goal=Goal(text="different"), steps=steps)
        planner = FixedPlanner(plan)
        result = await planner.create_plan(goal, object())  # type: ignore[arg-type]
        assert result.goal.text == "different"  # FixedPlanner ignores input goal


class TestSimpleLLMPlanner:
    async def test_parse_steps_from_llm_response(self, context: AgentRunContext) -> None:
        goal = Goal(text="Get weather and summarize")
        planner = SimpleLLMPlanner()
        plan = await planner.create_plan(goal, context)
        assert len(plan.steps) > 0
        assert plan.goal.text == "Get weather and summarize"
        assert plan.reasoning != ""

    async def test_creates_tool_and_llm_steps(self, context: AgentRunContext) -> None:
        goal = Goal(text="Do research")
        planner = SimpleLLMPlanner()
        plan = await planner.create_plan(goal, context)
        types = {s.type for s in plan.steps}
        assert StepType.TOOL_CALL in types
        assert StepType.LLM_COMPLETION in types

    async def test_empty_response_falls_back(self, tool_registry: ToolRegistry) -> None:
        context = AgentRunContext(
            llm_adapter=_EmptyAdapter(),
            tool_registry=tool_registry,
        )
        planner = SimpleLLMPlanner()
        goal = Goal(text="Just respond")
        plan = await planner.create_plan(goal, context)
        assert len(plan.steps) == 1
        assert plan.steps[0].type is StepType.LLM_COMPLETION
        assert plan.steps[0].prompt == "Just respond"

    async def test_respects_max_steps(self) -> None:
        planner = SimpleLLMPlanner(max_steps=3)
        assert planner._max_steps == 3

    async def test_parse_steps_valid_format(self) -> None:
        planner = SimpleLLMPlanner()
        goal = Goal(text="test")
        steps = planner._parse_steps(
            "STEP 1: tool_call | get_weather | get_weather\n"
            "STEP 2: llm_completion | summarize | Summarize the data\n",
            goal,
        )
        assert len(steps) == 2
        assert steps[0].type is StepType.TOOL_CALL
        assert steps[0].tool_name == "get_weather"
        assert steps[1].type is StepType.LLM_COMPLETION
        assert steps[1].prompt == "Summarize the data"

    async def test_parse_skips_invalid_lines(self) -> None:
        planner = SimpleLLMPlanner()
        goal = Goal(text="test")
        steps = planner._parse_steps(
            "Some preamble\n"
            "STEP 1: tool_call | echo | echo\n"
            "Invalid line here\n"
            "STEP 2: llm_completion | respond | Respond\n",
            goal,
        )
        assert len(steps) == 2
