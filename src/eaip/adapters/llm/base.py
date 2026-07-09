"""LLMAdapter protocol — the high-level contract for LLM adapters."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from eaip.adapters.llm.models import LLMRequest, LLMResponse, RunContext
from eaip.health.checks import HealthReport


@runtime_checkable
class LLMAdapter(Protocol):
    """Protocol for LLM adapters.

    An ``LLMAdapter`` wraps a :class:`~eaip.providers.base.Provider` and
    adds higher-level orchestration such as automatic tool-calling loops,
    context propagation, and health reporting.

    Implementations must provide:
    - ``name`` — unique adapter name.
    - ``version`` — semver string.
    - ``complete()`` — send a request and receive a response.
    - ``health()`` — return a health report.
    """

    name: str
    version: str

    async def complete(
        self,
        request: LLMRequest,
        *,
        context: RunContext | None = None,
    ) -> LLMResponse:
        """Send a completion request to the LLM.

        Args:
            request: The request parameters.
            context: Runtime context for tracing and isolation.

        Returns:
            An :class:`LLMResponse`.
        """
        ...

    async def health(self) -> HealthReport:
        """Return a health report for this adapter.

        Returns:
            A :class:`HealthReport`.
        """
        ...


__all__ = ["LLMAdapter"]
