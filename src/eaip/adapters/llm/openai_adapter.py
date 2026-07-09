"""OpenAI adapter — wraps an OpenAI-compatible provider with the LLMAdapter contract."""

from __future__ import annotations

from eaip.adapters.llm.models import LLMRequest, LLMResponse, RunContext
from eaip.adapters.llm.orchestration import ToolCallOrchestrator
from eaip.health.checks import HealthReport, HealthStatus
from eaip.providers.base import Provider
from eaip.tools.registry import ToolRegistry


class OpenAIAdapter:
    """LLMAdapter for OpenAI-compatible providers.

    Wraps an :class:`~eaip.providers.base.Provider` that speaks the OpenAI
    chat-completions wire format (e.g.
    :class:`~eaip.providers.openai_compat.OpenAICompatProvider`) and adds
    the tool-calling orchestration loop.

    Usage::

        adapter = OpenAIAdapter(provider=my_provider, tool_registry=my_registry)
        response = await adapter.complete(request, context=context)
    """

    name: str = "openai"
    version: str = "0.1.0"

    def __init__(
        self,
        provider: Provider,
        tool_registry: ToolRegistry | None = None,
        max_rounds: int = 10,
    ) -> None:
        """Initialize with a provider and optional tool registry."""
        self._provider = provider
        self._tool_registry = tool_registry or ToolRegistry()
        self._orchestrator = ToolCallOrchestrator(
            provider=provider,
            tool_registry=self._tool_registry,
            max_rounds=max_rounds,
        )

    async def complete(
        self,
        request: LLMRequest,
        *,
        context: RunContext | None = None,
    ) -> LLMResponse:
        """Send a completion request through the OpenAI-compatible provider."""
        return await self._orchestrator.execute(request, context=context or RunContext())

    async def health(self) -> HealthReport:
        """Check the underlying provider's health."""
        try:
            models = await self._provider.list_models()
            status = HealthStatus.HEALTHY
            message = f"provider reachable, {len(models)} models available"
        except Exception as exc:
            status = HealthStatus.UNHEALTHY
            message = str(exc)

        return HealthReport(
            component=self.name,
            status=status,
            message=message,
        )
