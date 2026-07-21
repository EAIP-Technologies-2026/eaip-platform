from __future__ import annotations

import pytest

from eaip.providers.exceptions import ModelNotFoundError
from eaip.providers.models import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ModelCapability,
    ModelFeature,
    ProviderInstance,
    ProviderStatus,
)
from eaip.providers.registry import ProviderRegistry
from eaip.providers.selector import ProviderSelector


class _FakeProvider:
    def __init__(self, name: str) -> None:
        self.name = name

    async def chat(self, request: ChatRequest) -> ChatResponse:
        return ChatResponse(
            model=request.model,
            provider=self.name,
            content=f"response from {self.name}",
        )

    async def chat_stream(self, request: ChatRequest):
        yield "fake"
        if False:
            yield ""

    async def list_models(self):
        return []


def _instance(
    name: str, model_id: str, priority: int = 0, status: ProviderStatus = ProviderStatus.AVAILABLE
) -> ProviderInstance:
    return ProviderInstance(
        name=name,
        provider_type="test",
        endpoint=f"http://{name}",
        models=(ModelCapability(model_id=model_id, provider=name, features=(ModelFeature.CHAT,)),),
        status=status,
        priority=priority,
    )


class TestProviderSelector:
    def test_select_by_model(self) -> None:
        registry = ProviderRegistry()
        registry.register(_instance("ollama", "llama3"))
        providers = {"ollama": _FakeProvider("ollama")}
        selector = ProviderSelector(registry, providers)
        provider = selector.select_provider("llama3")
        assert provider.name == "ollama"

    def test_select_prefers_higher_priority(self) -> None:
        registry = ProviderRegistry()
        registry.register(_instance("low", "llama3", priority=0))
        registry.register(_instance("high", "llama3", priority=100))
        providers = {"low": _FakeProvider("low"), "high": _FakeProvider("high")}
        selector = ProviderSelector(registry, providers)
        provider = selector.select_provider("llama3")
        assert provider.name == "high"

    def test_skips_unavailable(self) -> None:
        registry = ProviderRegistry()
        registry.register(_instance("down", "llama3", status=ProviderStatus.UNAVAILABLE))
        registry.register(_instance("up", "llama3", status=ProviderStatus.AVAILABLE))
        providers = {"down": _FakeProvider("down"), "up": _FakeProvider("up")}
        selector = ProviderSelector(registry, providers)
        provider = selector.select_provider("llama3")
        assert provider.name == "up"

    def test_raises_on_no_match(self) -> None:
        registry = ProviderRegistry()
        registry.register(_instance("ollama", "llama3"))
        providers = {"ollama": _FakeProvider("ollama")}
        selector = ProviderSelector(registry, providers)
        try:
            selector.select_provider("nonexistent-model")
            raise AssertionError()
        except ModelNotFoundError:
            pass

    @pytest.mark.asyncio
    async def test_chat_routing(self) -> None:
        registry = ProviderRegistry()
        registry.register(_instance("ollama", "llama3"))
        providers = {"ollama": _FakeProvider("ollama")}
        selector = ProviderSelector(registry, providers)

        msg = ChatMessage(role="user", content="hi")
        req = ChatRequest(model="llama3", messages=(msg,))
        resp = await selector.chat(req)
        assert "ollama" in resp.content

    @pytest.mark.asyncio
    async def test_failover_on_error(self) -> None:
        class _FailingProvider:
            def __init__(self, name: str) -> None:
                self.name = name

            async def chat(self, request: ChatRequest) -> ChatResponse:
                msg = f"failover from {self.name}"
                raise RuntimeError(msg)

            async def chat_stream(self, request: ChatRequest):
                yield ""
                if False:
                    yield ""

        class _WorkingProvider:
            def __init__(self, name: str) -> None:
                self.name = name

            async def chat(self, request: ChatRequest) -> ChatResponse:
                return ChatResponse(
                    model=request.model, provider=self.name, content="failover works"
                )

            async def chat_stream(self, request: ChatRequest):
                yield "ok"
                if False:
                    yield ""

        registry = ProviderRegistry()
        registry.register(_instance("primary", "llama3", priority=100))
        registry.register(_instance("backup", "llama3", priority=0))
        providers = {"primary": _FailingProvider("primary"), "backup": _WorkingProvider("backup")}
        selector = ProviderSelector(registry, providers)

        msg = ChatMessage(role="user", content="hi")
        req = ChatRequest(model="llama3", messages=(msg,))
        resp = await selector.chat(req)
        assert "failover works" in resp.content
