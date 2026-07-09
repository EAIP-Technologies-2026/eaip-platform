"""Tests for guardrail implementations."""

from __future__ import annotations

from eaip.agents.base import GuardrailResult
from eaip.agents.guardrails import CompositeGuardrail, NoopGuardrail
from eaip.agents.models import Step, StepType


class _SimpleGuardrail:
    name = "simple"

    def __init__(self, block: bool = False) -> None:
        self._block = block
        self.before_calls = 0
        self.after_calls = 0

    async def before_step(self, step: Step, context: object) -> GuardrailResult:
        self.before_calls += 1
        if self._block:
            return GuardrailResult(blocked=True, reason="blocked by simple guardrail")
        return GuardrailResult()

    async def after_step(self, step: Step, context: object) -> GuardrailResult:
        self.after_calls += 1
        if self._block:
            return GuardrailResult(blocked=True, reason="blocked after step")
        return GuardrailResult()


class TestNoopGuardrail:
    async def test_before_step_passes(self) -> None:
        g = NoopGuardrail()
        step = Step(id="s1", name="test", type=StepType.TOOL_CALL)
        result = await g.before_step(step, object())  # type: ignore[arg-type]
        assert result.blocked is False
        assert result.reason == ""

    async def test_after_step_passes(self) -> None:
        g = NoopGuardrail()
        step = Step(id="s1", name="test", type=StepType.TOOL_CALL)
        result = await g.after_step(step, object())  # type: ignore[arg-type]
        assert result.blocked is False

    def test_name(self) -> None:
        assert NoopGuardrail().name == "noop"


class TestCompositeGuardrail:
    async def test_empty_composite_passes(self) -> None:
        g = CompositeGuardrail([])
        step = Step(id="s1", name="test", type=StepType.TOOL_CALL)
        result = await g.before_step(step, context=object())  # type: ignore[arg-type]
        assert result.blocked is False

    async def test_runs_all_guardrails(self) -> None:
        g1 = _SimpleGuardrail()
        g2 = _SimpleGuardrail()
        composite = CompositeGuardrail([g1, g2])
        step = Step(id="s1", name="test", type=StepType.TOOL_CALL)
        await composite.before_step(step, context=object())  # type: ignore[arg-type]
        assert g1.before_calls == 1
        assert g2.before_calls == 1

    async def test_stops_at_first_block(self) -> None:
        g1 = _SimpleGuardrail(block=True)
        g2 = _SimpleGuardrail()
        composite = CompositeGuardrail([g1, g2])
        step = Step(id="s1", name="test", type=StepType.TOOL_CALL)
        result = await composite.before_step(step, context=object())  # type: ignore[arg-type]
        assert result.blocked is True
        assert g1.before_calls == 1
        assert g2.before_calls == 0  # Second guardrail was skipped

    async def test_after_step_runs_all(self) -> None:
        g1 = _SimpleGuardrail()
        g2 = _SimpleGuardrail()
        composite = CompositeGuardrail([g1, g2])
        step = Step(id="s1", name="test", type=StepType.TOOL_CALL)
        await composite.after_step(step, context=object())  # type: ignore[arg-type]
        assert g1.after_calls == 1
        assert g2.after_calls == 1

    def test_guardrails_property(self) -> None:
        g1 = _SimpleGuardrail()
        g2 = _SimpleGuardrail()
        composite = CompositeGuardrail([g1, g2])
        assert composite.guardrails == [g1, g2]
