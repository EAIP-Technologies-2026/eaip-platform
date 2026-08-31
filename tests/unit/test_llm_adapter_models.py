"""Tests for LLMRequest, LLMResponse, and RunContext models."""

from __future__ import annotations

import pytest

from eaip.adapters.llm.models import LLMRequest, LLMResponse, RunContext
from eaip.providers.models import ChatMessage, ToolCall


class TestLLMRequest:
    def test_required_fields(self) -> None:
        req = LLMRequest(
            model="gpt-4o",
            messages=(ChatMessage(role="user", content="Hello"),),
        )
        assert req.model == "gpt-4o"
        assert len(req.messages) == 1
        assert req.messages[0].role == "user"
        assert req.messages[0].content == "Hello"
        assert req.temperature == 0.7
        assert req.max_tokens is None
        assert req.stream is False
        assert req.tools == ()
        assert req.metadata == {}

    def test_with_all_fields(self) -> None:
        req = LLMRequest(
            model="gpt-4o",
            messages=(
                ChatMessage(role="system", content="Be helpful"),
                ChatMessage(role="user", content="Hi"),
            ),
            temperature=0.0,
            max_tokens=100,
            stream=True,
            tools=("get_weather", "calculator"),
            metadata={"session": "abc"},
        )
        assert req.model == "gpt-4o"
        assert len(req.messages) == 2
        assert req.temperature == 0.0
        assert req.max_tokens == 100
        assert req.stream is True
        assert req.tools == ("get_weather", "calculator")
        assert req.metadata == {"session": "abc"}

    def test_frozen(self) -> None:
        req = LLMRequest(
            model="gpt-4o",
            messages=(ChatMessage(role="user", content="Hi"),),
        )
        with pytest.raises(ValueError):
            req.model = "claude-3"

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValueError):
            LLMRequest(
                model="gpt-4o",
                messages=(),
                unknown="x",
            )  # type: ignore[call-arg]


class TestLLMResponse:
    def test_required_fields(self) -> None:
        resp = LLMResponse(model="gpt-4o", provider="openai", content="Hello!")
        assert resp.model == "gpt-4o"
        assert resp.provider == "openai"
        assert resp.content == "Hello!"
        assert resp.adapter == ""
        assert resp.finish_reason == "stop"
        assert resp.tool_calls is None
        assert resp.usage == {}
        assert resp.duration_ms == 0.0
        assert resp.rounds == 1

    def test_with_tool_calls(self) -> None:
        resp = LLMResponse(
            model="gpt-4o",
            provider="openai",
            content="",
            finish_reason="tool_calls",
            tool_calls=(ToolCall(id="call_1", name="get_weather", arguments={"loc": "NYC"}),),
            usage={"prompt_tokens": 10, "completion_tokens": 5},
            duration_ms=150.0,
            rounds=2,
        )
        assert resp.finish_reason == "tool_calls"
        assert resp.tool_calls is not None
        assert len(resp.tool_calls) == 1
        assert resp.tool_calls[0].name == "get_weather"
        assert resp.rounds == 2

    def test_frozen(self) -> None:
        resp = LLMResponse(model="gpt-4o", provider="openai", content="Hi")
        with pytest.raises(ValueError):
            resp.content = "changed"

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValueError):
            LLMResponse(model="gpt-4o", provider="openai", content="Hi", unknown=True)  # type: ignore[call-arg]


class TestRunContext:
    def test_defaults(self) -> None:
        ctx = RunContext()
        assert ctx.tenant_id == ""
        assert ctx.run_id == ""
        assert ctx.correlation_id == ""
        assert ctx.labels == {}
        assert ctx.max_tool_rounds == 10

    def test_with_values(self) -> None:
        ctx = RunContext(
            tenant_id="acme",
            run_id="run_123",
            correlation_id="corr_456",
            labels={"env": "test"},
            max_tool_rounds=5,
        )
        assert ctx.tenant_id == "acme"
        assert ctx.run_id == "run_123"
        assert ctx.correlation_id == "corr_456"
        assert ctx.labels == {"env": "test"}
        assert ctx.max_tool_rounds == 5

    def test_frozen(self) -> None:
        ctx = RunContext(tenant_id="acme")
        with pytest.raises(ValueError):
            ctx.tenant_id = "changed"

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValueError):
            RunContext(unknown=True)  # type: ignore[call-arg]
