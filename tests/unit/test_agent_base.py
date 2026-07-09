"""Tests for Agent Runtime protocols and guardrail result model."""

from __future__ import annotations

import pytest

from eaip.agents.base import Guardrail, GuardrailResult, Planner
from eaip.agents.models import Goal, Plan, Step, StepType


class TestPlannerProtocol:
    async def test_planner_protocol_runtime_checkable(self) -> None:
        class _TestPlanner:
            name = "test"

            async def create_plan(self, goal: Goal, context: object) -> Plan:
                return Plan(goal=goal, steps=())

        planner = _TestPlanner()
        assert isinstance(planner, Planner)

    async def test_planner_with_context_parameter(self) -> None:
        """Verify the planner signature accepts context."""

        class _Planner:
            name = "test"

            async def create_plan(self, goal: Goal, context: object) -> Plan:
                return Plan(goal=goal, steps=())

        p = _Planner()
        plan = await p.create_plan(Goal(text="test"), context=object())
        assert len(plan.steps) == 0


class TestGuardrailProtocol:
    async def test_guardrail_protocol_runtime_checkable(self) -> None:
        class _TestGuardrail:
            name = "test"

            async def before_step(self, step: Step, context: object) -> GuardrailResult:
                return GuardrailResult()

            async def after_step(self, step: Step, context: object) -> GuardrailResult:
                return GuardrailResult()

        g = _TestGuardrail()
        assert isinstance(g, Guardrail)

    async def test_guardrail_before_step(self) -> None:
        class _Guardrail:
            name = "test"

            async def before_step(self, step: Step, context: object) -> GuardrailResult:
                return GuardrailResult(blocked=True, reason="not allowed")

            async def after_step(self, step: Step, context: object) -> GuardrailResult:
                return GuardrailResult()

        g = _Guardrail()
        step = Step(id="s1", name="test", type=StepType.TOOL_CALL)
        result = await g.before_step(step, context=object())
        assert result.blocked is True
        assert result.reason == "not allowed"


class TestGuardrailResult:
    def test_defaults(self) -> None:
        r = GuardrailResult()
        assert r.blocked is False
        assert r.reason == ""
        assert r.modified_step is None

    def test_blocked(self) -> None:
        r = GuardrailResult(blocked=True, reason="blocked by policy")
        assert r.blocked is True
        assert r.reason == "blocked by policy"

    def test_frozen(self) -> None:
        r = GuardrailResult()
        with pytest.raises(ValueError):
            r.blocked = True  # type: ignore[misc]
