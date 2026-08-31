"""Tests for tool calling support in providers."""

from __future__ import annotations

import json

import httpx
import pytest

from eaip.providers.models import (
    ChatMessage,
    ChatRequest,
    ToolDefinition,
)
from eaip.providers.openai_compat import OpenAICompatProvider

_CHAT_WITH_TOOL_CALLS_RESP: bytes = json.dumps(
    {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1728000000,
        "model": "gpt-4",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_abc123",
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "arguments": '{"location": "NYC"}',
                            },
                        },
                        {
                            "id": "call_def456",
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "arguments": '{"location": "London"}',
                            },
                        },
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ],
        "usage": {"prompt_tokens": 50, "completion_tokens": 30, "total_tokens": 80},
    }
).encode()

_CHAT_NORMAL_RESP: bytes = json.dumps(
    {
        "id": "chatcmpl-456",
        "object": "chat.completion",
        "created": 1728000001,
        "model": "gpt-4",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Hello! How can I help you?",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }
).encode()

_FAILURE_RESP: bytes = json.dumps({"error": "bad request"}).encode()


class _MockTransport(httpx.AsyncBaseTransport):
    def __init__(self, content: bytes, status: int = 200) -> None:
        self._content = content
        self._status = status

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=self._status,
            content=self._content,
            headers={"Content-Type": "application/json"},
            request=request,
        )


class TestOpenAICompatToolCalling:
    @pytest.fixture
    def provider(self) -> OpenAICompatProvider:
        return OpenAICompatProvider(
            name="test-openai",
            endpoint="http://test-api/v1",
            api_key="sk-test",
        )

    async def test_chat_sends_tools_in_payload(self) -> None:
        transport = _MockTransport(_CHAT_NORMAL_RESP)
        provider = OpenAICompatProvider(
            name="test-openai",
            endpoint="http://test-api/v1",
            api_key="sk-test",
        )
        provider._client = httpx.AsyncClient(transport=transport)

        td = ToolDefinition(
            name="get_weather",
            description="Get weather for a location",
            parameters={
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                },
                "required": ["location"],
            },
        )
        msg = ChatMessage(role="user", content="weather in NYC?")
        req = ChatRequest(model="gpt-4", messages=(msg,), tools=(td,))

        resp = await provider.chat(req)
        assert resp.content == "Hello! How can I help you?"

    async def test_chat_parses_tool_calls(self) -> None:
        transport = _MockTransport(_CHAT_WITH_TOOL_CALLS_RESP)
        provider = OpenAICompatProvider(
            name="test-openai",
            endpoint="http://test-api/v1",
            api_key="sk-test",
        )
        provider._client = httpx.AsyncClient(transport=transport)

        td = ToolDefinition(name="get_weather", description="Get weather")
        msg = ChatMessage(role="user", content="weather?")
        req = ChatRequest(model="gpt-4", messages=(msg,), tools=(td,))

        resp = await provider.chat(req)
        assert resp.finish_reason == "tool_calls"
        assert resp.tool_calls is not None
        assert len(resp.tool_calls) == 2
        assert resp.tool_calls[0].id == "call_abc123"
        assert resp.tool_calls[0].name == "get_weather"
        assert resp.tool_calls[0].arguments["location"] == "NYC"
        assert resp.tool_calls[1].arguments["location"] == "London"

    async def test_chat_without_tools_returns_no_tool_calls(self) -> None:
        transport = _MockTransport(_CHAT_NORMAL_RESP)
        provider = OpenAICompatProvider(
            name="test-openai",
            endpoint="http://test-api/v1",
            api_key="sk-test",
        )
        provider._client = httpx.AsyncClient(transport=transport)

        msg = ChatMessage(role="user", content="hello")
        req = ChatRequest(model="gpt-4", messages=(msg,))

        resp = await provider.chat(req)
        assert resp.tool_calls is None
        assert resp.content == "Hello! How can I help you?"

    async def test_chat_with_malformed_tool_arguments(self) -> None:
        malformed = json.dumps(
            {
                "id": "chatcmpl-789",
                "object": "chat.completion",
                "created": 1728000002,
                "model": "gpt-4",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_bad",
                                    "type": "function",
                                    "function": {
                                        "name": "bad_tool",
                                        "arguments": "not valid json",
                                    },
                                },
                            ],
                        },
                        "finish_reason": "tool_calls",
                    }
                ],
                "usage": {},
            }
        ).encode()

        transport = _MockTransport(malformed)
        provider = OpenAICompatProvider(
            name="test-openai",
            endpoint="http://test-api/v1",
            api_key="sk-test",
        )
        provider._client = httpx.AsyncClient(transport=transport)

        msg = ChatMessage(role="user", content="do it")
        req = ChatRequest(model="gpt-4", messages=(msg,))

        resp = await provider.chat(req)
        assert resp.tool_calls is not None
        assert resp.tool_calls[0].arguments["_raw"] == "not valid json"

    async def test_chat_with_tools_and_normal_response(self) -> None:
        transport = _MockTransport(_CHAT_NORMAL_RESP)
        provider = OpenAICompatProvider(
            name="test-openai",
            endpoint="http://test-api/v1",
            api_key="sk-test",
        )
        provider._client = httpx.AsyncClient(transport=transport)

        td = ToolDefinition(name="get_weather")
        msg = ChatMessage(role="user", content="hello")
        req = ChatRequest(model="gpt-4", messages=(msg,), tools=(td,))

        resp = await provider.chat(req)
        assert resp.tool_calls is None
        assert resp.finish_reason == "stop"

    async def test_tool_calls_in_streaming_not_supported(self) -> None:
        transport = _MockTransport(_CHAT_NORMAL_RESP)
        provider = OpenAICompatProvider(
            name="test-openai",
            endpoint="http://test-api/v1",
            api_key="sk-test",
        )
        provider._client = httpx.AsyncClient(transport=transport)

        td = ToolDefinition(name="test", description="test")
        msg = ChatMessage(role="user", content="hello")
        req = ChatRequest(model="gpt-4", messages=(msg,), tools=(td,), stream=True)

        tokens: list[str] = []
        async for token in provider.chat_stream(req):
            tokens.append(token)  # noqa: PERF401

        assert tokens == []

    async def test_api_error_still_raises(self) -> None:
        transport = _MockTransport(_FAILURE_RESP, status=400)
        provider = OpenAICompatProvider(
            name="test-openai",
            endpoint="http://test-api/v1",
            api_key="sk-test",
        )
        provider._client = httpx.AsyncClient(transport=transport)

        td = ToolDefinition(name="test")
        msg = ChatMessage(role="user", content="hi")
        req = ChatRequest(model="gpt-4", messages=(msg,), tools=(td,))

        with pytest.raises(httpx.HTTPStatusError):
            await provider.chat(req)
