"""Tests for the AnthropicAdapter reference implementation."""

from __future__ import annotations

from collections.abc import AsyncIterator

from eaip.adapters.llm.anthropic_adapter import AnthropicAdapter
from eaip.adapters.llm.models import LLMRequest, RunContext
from eaip.health.checks import HealthStatus
from eaip.providers.models import ChatMessage, ChatRequest, ChatResponse, ModelCapability
from eaip.tools.registry import ToolRegistry


class _HealthyAnthropicProvider:
    name = "anthropic"

    async def chat(self, request: ChatRequest) -> ChatResponse:
        return ChatResponse(
            model="claude-3-opus",
            provider="anthropic",
            content="Hello from Anthropic",
            finish_reason="stop",
        )

    async def chat_stream(self, _request: ChatRequest) -> AsyncIterator[str]:
        return
        yield

    async def list_models(self) -> list[ModelCapability]:
        return [
            ModelCapability(model_id="claude-3-opus", provider="anthropic"),
            ModelCapability(model_id="claude-3-sonnet", provider="anthropic"),
        ]


class _UnhealthyAnthropicProvider:
    name = "anthropic"

    async def chat(self, request: ChatRequest) -> ChatResponse:
        return ChatResponse(
            model="claude-3-opus", provider="anthropic", content="", finish_reason="stop"
        )

    async def chat_stream(self, _request: ChatRequest) -> AsyncIterator[str]:
        return
        yield

    async def list_models(self) -> list[ModelCapability]:
        raise ConnectionError("API unreachable")


class TestAnthropicAdapter:
    async def test_complete_returns_response(self) -> None:
        adapter = AnthropicAdapter(provider=_HealthyAnthropicProvider())
        request = LLMRequest(
            model="claude-3-opus",
            messages=(ChatMessage(role="user", content="Hi"),),
        )
        response = await adapter.complete(request)
        assert response.content == "Hello from Anthropic"
        assert response.provider == "anthropic"
        assert response.rounds == 1

    async def test_complete_with_context(self) -> None:
        adapter = AnthropicAdapter(provider=_HealthyAnthropicProvider())
        request = LLMRequest(
            model="claude-3-opus",
            messages=(ChatMessage(role="user", content="Hi"),),
        )
        context = RunContext(tenant_id="acme", run_id="run_1")
        response = await adapter.complete(request, context=context)
        assert response.content == "Hello from Anthropic"

    async def test_complete_with_tools(self) -> None:
        registry = ToolRegistry()
        adapter = AnthropicAdapter(
            provider=_HealthyAnthropicProvider(), tool_registry=registry
        )
        request = LLMRequest(
            model="claude-3-opus",
            messages=(ChatMessage(role="user", content="Hi"),),
            tools=("some_tool",),
        )
        response = await adapter.complete(request)
        assert response.content == "Hello from Anthropic"

    async def test_health_healthy(self) -> None:
        adapter = AnthropicAdapter(provider=_HealthyAnthropicProvider())
        report = await adapter.health()
        assert report.status is HealthStatus.HEALTHY
        assert report.component == "anthropic"

    async def test_health_unhealthy(self) -> None:
        adapter = AnthropicAdapter(provider=_UnhealthyAnthropicProvider())
        report = await adapter.health()
        assert report.status is HealthStatus.UNHEALTHY
        assert report.component == "anthropic"

    def test_name_and_version(self) -> None:
        adapter = AnthropicAdapter(provider=_HealthyAnthropicProvider())
        assert adapter.name == "anthropic"
        assert adapter.version == "0.1.0"

    def test_default_tool_registry(self) -> None:
        adapter = AnthropicAdapter(provider=_HealthyAnthropicProvider())
        assert adapter._tool_registry is not None
        assert len(adapter._tool_registry) == 0
