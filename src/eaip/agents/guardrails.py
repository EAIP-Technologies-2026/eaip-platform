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


__all__ = ["CompositeGuardrail", "NoopGuardrail"]
