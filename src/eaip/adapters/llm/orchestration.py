"""Tool-calling orchestration — the LLM→tool→LLM loop."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.adapters.llm.exceptions import MaxToolRoundsError, ToolExecutionError
from eaip.adapters.llm.models import LLMRequest, LLMResponse, RunContext
from eaip.providers.models import ChatMessage, ChatRequest, ToolCall, ToolDefinition, ToolResult

if TYPE_CHECKING:
    from eaip.providers.base import Provider
    from eaip.tools.registry import ToolRegistry


class ToolCallOrchestrator:
    """Orchestrates the tool-calling loop.

    Given a :class:`~eaip.providers.base.Provider` and a
    :class:`~eaip.tools.registry.ToolRegistry`, this class handles the
    iterative call → parse tool calls → execute tools → feed results back →
    call again cycle.

    Usage::

        orchestrator = ToolCallOrchestrator(provider, registry, max_rounds=10)
        response = await orchestrator.execute(request, context)
    """

    def __init__(
        self,
        provider: Provider,
        tool_registry: ToolRegistry,
        max_rounds: int = 10,
    ) -> None:
        """Initialize the orchestrator with a provider and tool registry."""
        self._provider = provider
        self._tool_registry = tool_registry
        self._max_rounds = max_rounds

    @property
    def provider(self) -> Provider:
        """The underlying provider."""
        return self._provider

    @property
    def tool_registry(self) -> ToolRegistry:
        """The tool registry."""
        return self._tool_registry

    @property
    def max_rounds(self) -> int:
        """Maximum tool-calling rounds."""
        return self._max_rounds

    async def execute(
        self,
        request: LLMRequest,
        context: RunContext | None = None,
    ) -> LLMResponse:
        """Execute the full request, running the tool loop if needed.

        Args:
            request: The LLM request.
            context: Runtime context.

        Returns:
            The final LLM response.

        Raises:
            MaxToolRoundsError: If the tool loop exceeds the maximum rounds.
            ToolExecutionError: If a tool execution fails.
        """
        ctx = context or RunContext()
        max_rounds = min(self._max_rounds, ctx.max_tool_rounds)

        tool_defs = self._resolve_tools(request.tools)
        messages = list(request.messages)
        total_duration = 0.0
        round_count = 0

        for round_count in range(1, max_rounds + 1):
            chat_request = ChatRequest(
                model=request.model,
                messages=tuple(messages),
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=False,
                tools=tool_defs or None,
                metadata=request.metadata,
            )

            start = time.monotonic()
            chat_response = await self._provider.chat(chat_request)
            elapsed = time.monotonic() - start
            total_duration += elapsed

            response_tool_calls = chat_response.tool_calls

            if not response_tool_calls:
                return LLMResponse(
                    model=chat_response.model,
                    provider=chat_response.provider,
                    content=chat_response.content,
                    finish_reason=chat_response.finish_reason,
                    tool_calls=None,
                    usage=chat_response.usage,
                    duration_ms=total_duration * 1000,
                    rounds=round_count,
                )

            messages.append(
                ChatMessage(role="assistant", content=chat_response.content)
            )

            for tc in response_tool_calls:
                result = await self._execute_single_tool(tc)
                messages.append(
                    ChatMessage(
                        role="tool",
                        content=result.content,
                    )
                )

        raise MaxToolRoundsError(
            f"Tool-calling loop exceeded maximum rounds ({max_rounds})",
            context={"rounds": max_rounds, "model": request.model},
        )

    def _resolve_tools(
        self,
        tool_names: tuple[str, ...],
    ) -> tuple[ToolDefinition, ...]:
        """Resolve tool names to ToolDefinitions via the registry."""
        if not tool_names:
            return ()

        defs: list[ToolDefinition] = []
        for name in tool_names:
            tool = self._tool_registry.try_get(name)
            if tool is not None:
                defs.append(
                    ToolDefinition(
                        name=tool.name,
                        description=tool.description,
                        parameters=tool.parameters,
                    )
                )
        return tuple(defs)

    async def _execute_single_tool(self, tc: ToolCall) -> ToolResult:
        """Execute a single tool call, catching errors."""
        tool = self._tool_registry.try_get(tc.name)
        if tool is None:
            return ToolResult(
                tool_call_id=tc.id,
                content=f"Error: tool {tc.name!r} not found",
                is_error=True,
            )

        try:
            result = await tool.execute(**tc.arguments)
            return ToolResult(tool_call_id=tc.id, content=result, is_error=False)
        except Exception as exc:
            raise ToolExecutionError(
                f"Tool {tc.name!r} execution failed: {exc}",
                context={"tool": tc.name, "arguments": tc.arguments},
                cause=exc,
            ) from exc


__all__ = ["ToolCallOrchestrator"]
