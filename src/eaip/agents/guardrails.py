"""Guardrail implementations — pre/post step hooks."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from eaip.agents.base import GuardrailResult
from eaip.agents.models import Step

if TYPE_CHECKING:
    from eaip.agents.runtime import AgentRunContext


class NoopGuardrail:
    """A guardrail that passes all steps through unchanged."""

    name: str = "noop"

    async def before_step(
        self,
        _step: Step,
        _context: AgentRunContext,
    ) -> GuardrailResult:
        """Pass every step through unmodified."""
        return GuardrailResult()

    async def after_step(
        self,
        _step: Step,
        _context: AgentRunContext,
    ) -> GuardrailResult:
        """Pass every completed step through unmodified."""
        return GuardrailResult()


class CompositeGuardrail:
    """Runs multiple guardrails in sequence and aggregates results.

    If any guardrail blocks a step, the remaining guardrails are skipped.
    """

    name: str = "composite"

    def __init__(self, guardrails: list[Any]) -> None:  # noqa: D107
        self._guardrails = list(guardrails)

    @property
    def guardrails(self) -> list[Any]:
        """Return the contained guardrails."""
        return list(self._guardrails)

    async def before_step(
        self,
        step: Step,
        context: AgentRunContext,
    ) -> GuardrailResult:
        """Run all guardrail before_step hooks.

        Stops at the first blocked result.
        """
        for g in self._guardrails:
            result: GuardrailResult = await g.before_step(step, context)
            if result.blocked:
                return result
            if result.modified_step is not None:
                step = result.modified_step
        return GuardrailResult()

    async def after_step(
        self,
        step: Step,
        context: AgentRunContext,
    ) -> GuardrailResult:
        """Run all guardrail after_step hooks.

        Stops at the first blocked result.
        """
        for g in self._guardrails:
            result: GuardrailResult = await g.after_step(step, context)
            if result.blocked:
                return result
        return GuardrailResult()


class EngineGuardrail:
    """Agent Guardrail adapter that delegates to GuardrailsEngine."""

    name: str = "engine_guardrail"

    def __init__(self, engine: Any | None = None) -> None:
        from eaip.guardrails.service import GuardrailsEngine

        self._engine = engine or GuardrailsEngine()

    async def before_step(
        self,
        step: Step,
        _context: AgentRunContext,
    ) -> GuardrailResult:
        text_to_check = step.prompt or step.name
        injection_res = self._engine.check_prompt_injection(text_to_check)
        if not injection_res.passed:
            return GuardrailResult(blocked=True, reason=injection_res.message)

        if step.prompt:
            masked_prompt, _ = self._engine.mask_pii(step.prompt)
            if masked_prompt != step.prompt:
                modified = step.model_copy(update={"prompt": masked_prompt})
                return GuardrailResult(blocked=False, modified_step=modified)

        return GuardrailResult()

    async def after_step(
        self,
        step: Step,
        _context: AgentRunContext,
    ) -> GuardrailResult:
        if step.output:
            rule_results = self._engine.evaluate_text(step.output)
            failed = [r for r in rule_results if not r.passed]
            if failed:
                return GuardrailResult(
                    blocked=True,
                    reason=f"Output policy violation: {failed[0].message}",
                )
        return GuardrailResult()


__all__ = ["CompositeGuardrail", "EngineGuardrail", "NoopGuardrail"]

