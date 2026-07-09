"""Tests for the OpenAIAdapter reference implementation."""

from __future__ import annotations

from collections.abc import AsyncIterator

from eaip.adapters.llm.models import LLMRequest, RunContext
from eaip.adapters.llm.openai_adapter import OpenAIAdapter
from eaip.health.checks import HealthStatus
from eaip.providers.models import ChatMessage, ChatRequest, ChatResponse, ModelCapability
from eaip.tools.registry import ToolRegistry


class _DummyTool:
    name = "echo"
    description = "Echo back input"

    @property
    def parameters(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        }

    async def execute(self, **kwargs: object) -> str:
        return str(kwargs.get("message", ""))


class _HealthyProvider:
    name = "openai"

    async def chat(self, request: ChatRequest) -> ChatResponse:
        return ChatResponse(
            model="gpt-4o",
            provider="openai",
            content="Hello from OpenAI",
            finish_reason="stop",
        )

    async def chat_stream(self, _request: ChatRequest) -> AsyncIterator[str]:
        return
        yield

    async def list_models(self) -> list[ModelCapability]:
        return [
            ModelCapability(model_id="gpt-4o", provider="openai"),
            ModelCapability(model_id="gpt-4o-mini", provider="openai"),
        ]


class _UnhealthyProvider:
    name = "openai"

    async def chat(self, request: ChatRequest) -> ChatResponse:
        return ChatResponse(
            model="gpt-4o", provider="openai", content="", finish_reason="stop"
        )

    async def chat_stream(self, _request: ChatRequest) -> AsyncIterator[str]:
        return
        yield

    async def list_models(self) -> list[ModelCapability]:
        raise ConnectionError("Connection refused")


class TestOpenAIAdapter:
    async def test_complete_returns_response(self) -> None:
        adapter = OpenAIAdapter(provider=_HealthyProvider())
        request = LLMRequest(
            model="gpt-4o",
            messages=(ChatMessage(role="user", content="Hi"),),
        )
        response = await adapter.complete(request)
        assert response.content == "Hello from OpenAI"
        assert response.provider == "openai"
        assert response.rounds == 1

    async def test_complete_with_context(self) -> None:
        adapter = OpenAIAdapter(provider=_HealthyProvider())
        request = LLMRequest(
            model="gpt-4o",
            messages=(ChatMessage(role="user", content="Hi"),),
        )
        context = RunContext(tenant_id="acme", run_id="run_1")
        response = await adapter.complete(request, context=context)
        assert response.content == "Hello from OpenAI"

    async def test_complete_with_tools(self) -> None:
        registry = ToolRegistry()
        registry.register(_DummyTool())
        adapter = OpenAIAdapter(provider=_HealthyProvider(), tool_registry=registry)
        request = LLMRequest(
            model="gpt-4o",
            messages=(ChatMessage(role="user", content="Echo hello"),),
            tools=("echo",),
        )
        response = await adapter.complete(request)
        assert response.content == "Hello from OpenAI"

    async def test_health_healthy(self) -> None:
        adapter = OpenAIAdapter(provider=_HealthyProvider())
        report = await adapter.health()
        assert report.status is HealthStatus.HEALTHY
        assert report.component == "openai"

    async def test_health_unhealthy(self) -> None:
        adapter = OpenAIAdapter(provider=_UnhealthyProvider())
        report = await adapter.health()
        assert report.status is HealthStatus.UNHEALTHY
        assert report.component == "openai"

    def test_name_and_version(self) -> None:
        adapter = OpenAIAdapter(provider=_HealthyProvider())
        assert adapter.name == "openai"
        assert adapter.version == "0.1.0"

    def test_default_tool_registry(self) -> None:
        adapter = OpenAIAdapter(provider=_HealthyProvider())
        assert adapter._tool_registry is not None
        assert len(adapter._tool_registry) == 0
