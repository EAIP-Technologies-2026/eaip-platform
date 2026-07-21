from __future__ import annotations

from eaip.providers.models import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ModelCapability,
    ModelFeature,
    ProviderInstance,
    ProviderStatus,
)


class TestProviderStatus:
    def test_enum_values(self) -> None:
        assert ProviderStatus.AVAILABLE.value == "available"
        assert ProviderStatus.UNAVAILABLE.value == "unavailable"


class TestModelCapability:
    def test_minimal(self) -> None:
        mc = ModelCapability(model_id="llama3", provider="ollama")
        assert mc.model_id == "llama3"
        assert mc.features == (ModelFeature.CHAT,)
        assert mc.max_tokens == 4096

    def test_frozen(self) -> None:
        mc = ModelCapability(model_id="a", provider="b")
        import pydantic

        try:
            mc.model_id = "c"
            raise AssertionError()
        except pydantic.ValidationError:
            pass


class TestChatMessage:
    def test_create(self) -> None:
        m = ChatMessage(role="user", content="hello")
        assert m.role == "user"
        assert m.content == "hello"

    def test_frozen(self) -> None:
        m = ChatMessage(role="user", content="hi")
        import pydantic

        try:
            m.content = "changed"
            raise AssertionError()
        except pydantic.ValidationError:
            pass


class TestChatRequest:
    def test_minimal(self) -> None:
        msg = ChatMessage(role="user", content="hello")
        req = ChatRequest(model="llama3", messages=(msg,))
        assert req.model == "llama3"
        assert req.temperature == 0.7
        assert req.stream is False

    def test_with_options(self) -> None:
        msg = ChatMessage(role="user", content="hello")
        req = ChatRequest(
            model="gpt4", messages=(msg,), temperature=0.1, max_tokens=100, stream=True
        )
        assert req.temperature == 0.1
        assert req.max_tokens == 100
        assert req.stream is True


class TestChatResponse:
    def test_minimal(self) -> None:
        r = ChatResponse(model="llama3", provider="ollama", content="Hello!")
        assert r.content == "Hello!"
        assert r.finish_reason == "stop"
        assert r.duration_ms == 0.0

    def test_frozen(self) -> None:
        r = ChatResponse(model="a", provider="b", content="c")
        import pydantic

        try:
            r.content = "changed"
            raise AssertionError()
        except pydantic.ValidationError:
            pass


class TestProviderInstance:
    def test_minimal(self) -> None:
        inst = ProviderInstance(
            name="ollama", provider_type="ollama", endpoint="http://localhost:11434"
        )
        assert inst.name == "ollama"
        assert inst.status is ProviderStatus.UNAVAILABLE
        assert inst.priority == 0

    def test_full(self) -> None:
        mc = ModelCapability(model_id="llama3", provider="ollama")
        inst = ProviderInstance(
            name="ollama",
            provider_type="ollama",
            endpoint="http://localhost:11434",
            default_model="llama3",
            models=(mc,),
            priority=10,
        )
        assert len(inst.models) == 1
        assert inst.priority == 10

    def test_frozen(self) -> None:
        inst = ProviderInstance(name="a", provider_type="b", endpoint="c")
        import pydantic

        try:
            inst.name = "changed"
            raise AssertionError()
        except pydantic.ValidationError:
            pass
