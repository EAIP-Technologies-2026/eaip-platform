"""Tests for Agent Runtime models."""

from __future__ import annotations

import pytest

from eaip.agents.models import (
    AgentSpec,
    Goal,
    Plan,
    RunRecord,
    RunStatus,
    Step,
    StepStatus,
    StepType,
)


class TestGoal:
    def test_required_fields(self) -> None:
        g = Goal(text="Do something")
        assert g.text == "Do something"
        assert g.constraints == ()
        assert g.metadata == {}

    def test_with_all_fields(self) -> None:
        g = Goal(
            text="Build a website",
            constraints=("use python", "be fast"),
            metadata={"priority": "high"},
        )
        assert g.text == "Build a website"
        assert g.constraints == ("use python", "be fast")
        assert g.metadata == {"priority": "high"}

    def test_frozen(self) -> None:
        g = Goal(text="test")
        with pytest.raises(ValueError):
            g.text = "changed"

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValueError):
            Goal(text="test", unknown=True)  # type: ignore[call-arg]


class TestStep:
    def test_tool_call_step(self) -> None:
        s = Step(id="step_1", name="get_weather", type=StepType.TOOL_CALL, tool_name="weather")
        assert s.id == "step_1"
        assert s.type is StepType.TOOL_CALL
        assert s.tool_name == "weather"
        assert s.status is StepStatus.PENDING

    def test_llm_completion_step(self) -> None:
        s = Step(
            id="step_2", name="summarize", type=StepType.LLM_COMPLETION, prompt="Summarize the data"
        )
        assert s.type is StepType.LLM_COMPLETION
        assert s.prompt == "Summarize the data"

    def test_completed_step(self) -> None:
        s = Step(
            id="step_1",
            name="echo",
            type=StepType.TOOL_CALL,
            status=StepStatus.COMPLETED,
            output="Hello",
            duration_ms=50.0,
        )
        assert s.status is StepStatus.COMPLETED
        assert s.output == "Hello"
        assert s.duration_ms == 50.0

    def test_frozen(self) -> None:
        s = Step(id="s1", name="test", type=StepType.TOOL_CALL)
        with pytest.raises(ValueError):
            s.name = "changed"


class TestPlan:
    def test_create_plan(self) -> None:
        goal = Goal(text="Test")
        steps = (
            Step(id="s1", name="step1", type=StepType.TOOL_CALL, tool_name="echo"),
            Step(id="s2", name="step2", type=StepType.LLM_COMPLETION, prompt="done"),
        )
        p = Plan(goal=goal, steps=steps, reasoning="Just do it")
        assert p.goal.text == "Test"
        assert len(p.steps) == 2
        assert p.reasoning == "Just do it"

    def test_frozen(self) -> None:
        p = Plan(goal=Goal(text="x"), steps=())
        with pytest.raises(ValueError):
            p.reasoning = "changed"


class TestAgentSpec:
    def test_required_fields(self) -> None:
        spec = AgentSpec(id="agent_1", name="Helper")
        assert spec.id == "agent_1"
        assert spec.name == "Helper"
        assert spec.version == "0.1.0"
        assert spec.tools == ()

    def test_with_tools(self) -> None:
        spec = AgentSpec(
            id="a1",
            name="Researcher",
            tools=("search", "summarize"),
            max_steps=50,
        )
        assert spec.tools == ("search", "summarize")
        assert spec.max_steps == 50


class TestRunRecord:
    def test_pending_run(self) -> None:
        run = RunRecord(id="run_1", agent_id="agent_1", goal=Goal(text="test"))
        assert run.status is RunStatus.PENDING
        assert run.steps == ()
        assert run.result == ""
        assert run.error is None

    def test_with_plan_and_steps(self) -> None:
        steps = (Step(id="s1", name="echo", type=StepType.TOOL_CALL),)
        plan = Plan(goal=Goal(text="test"), steps=steps)
        run = RunRecord(
            id="run_1",
            agent_id="agent_1",
            goal=Goal(text="test"),
            plan=plan,
            steps=steps,
            status=RunStatus.COMPLETED,
            result="done",
            duration_ms=100.0,
        )
        assert run.plan is not None
        assert len(run.steps) == 1
        assert run.status is RunStatus.COMPLETED
        assert run.result == "done"

    def test_frozen(self) -> None:
        run = RunRecord(id="r1", agent_id="a1", goal=Goal(text="x"))
        with pytest.raises(ValueError):
            run.status = RunStatus.RUNNING  # type: ignore[misc]
