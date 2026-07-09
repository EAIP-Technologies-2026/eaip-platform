"""Tests for the ToolCallOrchestrator tool-calling loop."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from eaip.adapters.llm.exceptions import MaxToolRoundsError, ToolExecutionError
from eaip.adapters.llm.models import LLMRequest, RunContext
from eaip.adapters.llm.orchestration import ToolCallOrchestrator
from eaip.providers.models import ChatMessage, ChatRequest, ChatResponse, ModelCapability, ToolCall
from eaip.tools.registry import ToolRegistry


class _SimpleTool:
    """A minimal Tool implementation for testing."""

    def __init__(self, name: str, description: str = "") -> None:
        self.name = name
        self.description = description

    @property
    def parameters(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    async def execute(self, **kwargs: object) -> str:
        return f"{self.name} executed with {kwargs}"


class _FailingTool:
    """A tool that raises during execution."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.description = ""

    @property
    def parameters(self) -> dict[str, object]:
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self, **kwargs: object) -> str:
        msg = f"{self.name} boom"
        raise RuntimeError(msg)


class _MockProvider:
    """A provider that returns configurable ChatResponses."""

    name = "mock"

    def __init__(self) -> None:
        self.call_count = 0
        self._responses: list[ChatResponse] = []
        self._requests: list[ChatRequest] = []

    def add_response(self, response: ChatResponse) -> None:
        self._responses.append(response)

    async def chat(self, request: ChatRequest) -> ChatResponse:
        self.call_count += 1
        self._requests.append(request)
        if not self._responses:
            return ChatResponse(
                model=request.model,
                provider="mock",
                content="Final answer",
                finish_reason="stop",
            )
        return self._responses.pop(0)

    async def chat_stream(self, _request: ChatRequest) -> AsyncIterator[str]:
        return
        yield

    async def list_models(self) -> list[ModelCapability]:
        return [ModelCapability(model_id="gpt-4o", provider="mock")]


@pytest.fixture
def tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(_SimpleTool("get_time", "Get the current time"))
    registry.register(_SimpleTool("calculator", "Perform math"))
    return registry


@pytest.fixture
def mock_provider() -> _MockProvider:
    return _MockProvider()


@pytest.fixture
def request_no_tools() -> LLMRequest:
    return LLMRequest(
        model="gpt-4o",
        messages=(ChatMessage(role="user", content="Hello"),),
    )


@pytest.fixture
def request_with_tools() -> LLMRequest:
    return LLMRequest(
        model="gpt-4o",
        messages=(ChatMessage(role="user", content="What time is it?"),),
        tools=("get_time", "calculator"),
    )


@pytest.fixture
def request_with_nonexistent_tool() -> LLMRequest:
    return LLMRequest(
        model="gpt-4o",
        messages=(ChatMessage(role="user", content="Do something"),),
        tools=("nonexistent_tool",),
    )


class TestToolCallOrchestrator:
    async def test_no_tools_returns_response_directly(
        self,
        mock_provider: _MockProvider,
        request_no_tools: LLMRequest,
    ) -> None:
        orchestrator = ToolCallOrchestrator(mock_provider, ToolRegistry())
        response = await orchestrator.execute(request_no_tools)

        assert response.content == "Final answer"
        assert response.rounds == 1
        assert mock_provider.call_count == 1

    async def test_no_tool_requests_returns_directly(
        self,
        mock_provider: _MockProvider,
        request_no_tools: LLMRequest,
    ) -> None:
        orchestrator = ToolCallOrchestrator(mock_provider, ToolRegistry())
        mock_provider.add_response(
            ChatResponse(
                model="gpt-4o",
                provider="mock",
                content="Hello back",
                finish_reason="stop",
            )
        )
        response = await orchestrator.execute(request_no_tools)

        assert response.content == "Hello back"
        assert response.rounds == 1
        assert mock_provider.call_count == 1

    async def test_tool_called_and_result_returned(
        self,
        mock_provider: _MockProvider,
        tool_registry: ToolRegistry,
        request_with_tools: LLMRequest,
    ) -> None:
        orchestrator = ToolCallOrchestrator(mock_provider, tool_registry)

        mock_provider.add_response(
            ChatResponse(
                model="gpt-4o",
                provider="mock",
                content="",
                finish_reason="tool_calls",
                tool_calls=(
                    ToolCall(id="call_1", name="get_time", arguments={}),
                ),
            )
        )

        response = await orchestrator.execute(request_with_tools)

        assert response.content == "Final answer"
        assert response.rounds == 2
        assert mock_provider.call_count == 2

    async def test_multiple_tool_calls_in_one_round(
        self,
        mock_provider: _MockProvider,
        tool_registry: ToolRegistry,
        request_with_tools: LLMRequest,
    ) -> None:
        orchestrator = ToolCallOrchestrator(mock_provider, tool_registry)

        mock_provider.add_response(
            ChatResponse(
                model="gpt-4o",
                provider="mock",
                content="",
                finish_reason="tool_calls",
                tool_calls=(
                    ToolCall(id="call_1", name="get_time", arguments={}),
                    ToolCall(id="call_2", name="calculator", arguments={"expr": "2+2"}),
                ),
            )
        )

        response = await orchestrator.execute(request_with_tools)

        assert response.content == "Final answer"
        assert response.rounds == 2
        assert mock_provider.call_count == 2

        last_request = mock_provider._requests[-1]
        tool_messages = [m for m in last_request.messages if m.role == "tool"]
        assert len(tool_messages) == 2

    async def test_max_rounds_exceeded(
        self,
        mock_provider: _MockProvider,
        tool_registry: ToolRegistry,
        request_with_tools: LLMRequest,
    ) -> None:
        orchestrator = ToolCallOrchestrator(
            mock_provider, tool_registry, max_rounds=3
        )
        context = RunContext(max_tool_rounds=2)

        mock_provider.add_response(
            ChatResponse(
                model="gpt-4o",
                provider="mock",
                content="",
                finish_reason="tool_calls",
                tool_calls=(
                    ToolCall(id="call_1", name="get_time", arguments={}),
                ),
            )
        )
        mock_provider.add_response(
            ChatResponse(
                model="gpt-4o",
                provider="mock",
                content="",
                finish_reason="tool_calls",
                tool_calls=(
                    ToolCall(id="call_2", name="get_time", arguments={}),
                ),
            )
        )

        with pytest.raises(MaxToolRoundsError) as excinfo:
            await orchestrator.execute(request_with_tools, context=context)

        assert "exceeded maximum rounds" in str(excinfo.value).lower()
        assert excinfo.value.context.get("rounds") == 2

    async def test_tool_execution_error(
        self,
        mock_provider: _MockProvider,
        request_with_tools: LLMRequest,
    ) -> None:
        registry = ToolRegistry()
        registry.register(_FailingTool("get_time"))

        orchestrator = ToolCallOrchestrator(mock_provider, registry)

        mock_provider.add_response(
            ChatResponse(
                model="gpt-4o",
                provider="mock",
                content="",
                finish_reason="tool_calls",
                tool_calls=(
                    ToolCall(id="call_1", name="get_time", arguments={}),
                ),
            )
        )

        with pytest.raises(ToolExecutionError) as excinfo:
            await orchestrator.execute(request_with_tools)

        assert "get_time" in str(excinfo.value)

    async def test_nonexistent_tool_returns_error_result(
        self,
        mock_provider: _MockProvider,
        tool_registry: ToolRegistry,
        request_with_nonexistent_tool: LLMRequest,
    ) -> None:
        orchestrator = ToolCallOrchestrator(mock_provider, tool_registry)

        mock_provider.add_response(
            ChatResponse(
                model="gpt-4o",
                provider="mock",
                content="",
                finish_reason="tool_calls",
                tool_calls=(
                    ToolCall(id="call_1", name="nonexistent_tool", arguments={}),
                ),
            )
        )

        response = await orchestrator.execute(request_with_nonexistent_tool)

        assert response.content == "Final answer"
        assert response.rounds == 2

        last_request = mock_provider._requests[-1]
        tool_messages = [m for m in last_request.messages if m.role == "tool"]
        assert len(tool_messages) == 1
        assert "not found" in tool_messages[0].content

    async def test_provider_and_registry_properties(
        self,
        mock_provider: _MockProvider,
        tool_registry: ToolRegistry,
    ) -> None:
        orchestrator = ToolCallOrchestrator(mock_provider, tool_registry, max_rounds=5)

        assert orchestrator.provider is mock_provider
        assert orchestrator.tool_registry is tool_registry
        assert orchestrator.max_rounds == 5

    async def test_rounds_tracked_correctly(
        self,
        mock_provider: _MockProvider,
        tool_registry: ToolRegistry,
    ) -> None:
        orchestrator = ToolCallOrchestrator(mock_provider, tool_registry)

        mock_provider.add_response(
            ChatResponse(
                model="gpt-4o",
                provider="mock",
                content="",
                finish_reason="tool_calls",
                tool_calls=(
                    ToolCall(id="c1", name="get_time", arguments={}),
                ),
            )
        )
        mock_provider.add_response(
            ChatResponse(
                model="gpt-4o",
                provider="mock",
                content="",
                finish_reason="tool_calls",
                tool_calls=(
                    ToolCall(id="c2", name="get_time", arguments={}),
                ),
            )
        )

        response = await orchestrator.execute(
            LLMRequest(
                model="gpt-4o",
                messages=(ChatMessage(role="user", content="Count"),),
                tools=("get_time",),
            ),
            context=RunContext(max_tool_rounds=5),
        )

        assert response.rounds == 3
        assert response.content == "Final answer"
