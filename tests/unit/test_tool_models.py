"""Tests for ToolDefinition, ToolCall, and ToolResult models."""

from __future__ import annotations

import json

import pytest

from eaip.providers.models import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ToolCall,
    ToolDefinition,
    ToolResult,
)


class TestToolDefinition:
    def test_required_fields(self) -> None:
        td = ToolDefinition(name="get_weather")
        assert td.name == "get_weather"
        assert td.description == ""
        assert td.parameters == {}

    def test_with_description(self) -> None:
        td = ToolDefinition(
            name="get_weather",
            description="Get current weather for a location",
        )
        assert td.description == "Get current weather for a location"

    def test_with_parameters(self) -> None:
        td = ToolDefinition(
            name="get_weather",
            parameters={
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "unit": {"type": "string", "enum": ["c", "f"]},
                },
                "required": ["location"],
            },
        )
        assert td.parameters["type"] == "object"
        assert "location" in td.parameters["properties"]

    def test_frozen(self) -> None:
        td = ToolDefinition(name="test")
        with pytest.raises(ValueError):
            td.name = "changed"  # type: ignore[misc]

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValueError):
            ToolDefinition(name="test", unknown="x")  # type: ignore[call-arg]


class TestToolCall:
    def test_required_fields(self) -> None:
        tc = ToolCall(id="call_123", name="get_weather")
        assert tc.id == "call_123"
        assert tc.name == "get_weather"
        assert tc.arguments == {}

    def test_with_arguments(self) -> None:
        tc = ToolCall(
            id="call_456",
            name="calculator",
            arguments={"expression": "2 + 2"},
        )
        assert tc.arguments["expression"] == "2 + 2"

    def test_frozen(self) -> None:
        tc = ToolCall(id="c1", name="test")
        with pytest.raises(ValueError):
            tc.name = "changed"  # type: ignore[misc]

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValueError):
            ToolCall(id="c1", name="t", unknown=True)  # type: ignore[call-arg]


class TestToolResult:
    def test_required_fields(self) -> None:
        tr = ToolResult(tool_call_id="call_123", content="sunny, 72°F")
        assert tr.tool_call_id == "call_123"
        assert tr.content == "sunny, 72°F"
        assert tr.is_error is False

    def test_error_result(self) -> None:
        tr = ToolResult(
            tool_call_id="call_999",
            content="division by zero",
            is_error=True,
        )
        assert tr.is_error is True

    def test_frozen(self) -> None:
        tr = ToolResult(tool_call_id="c1", content="ok")
        with pytest.raises(ValueError):
            tr.content = "changed"  # type: ignore[misc]

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValueError):
            ToolResult(tool_call_id="c1", content="x", unknown="y")  # type: ignore[call-arg]


class TestChatRequestWithTools:
    def test_without_tools(self) -> None:
        msg = ChatMessage(role="user", content="hello")
        req = ChatRequest(model="gpt-4", messages=(msg,))
        assert req.tools is None

    def test_with_tools(self) -> None:
        msg = ChatMessage(role="user", content="what's the weather?")
        td = ToolDefinition(name="get_weather", description="Get weather")
        req = ChatRequest(model="gpt-4", messages=(msg,), tools=(td,))
        assert req.tools is not None
        assert len(req.tools) == 1
        assert req.tools[0].name == "get_weather"

    def test_multiple_tools(self) -> None:
        msg = ChatMessage(role="user", content="do both")
        t1 = ToolDefinition(name="tool_a")
        t2 = ToolDefinition(name="tool_b")
        req = ChatRequest(model="gpt-4", messages=(msg,), tools=(t1, t2))
        assert len(req.tools) == 2

    def test_frozen_prevents_mutation(self) -> None:
        msg = ChatMessage(role="user", content="hi")
        req = ChatRequest(model="gpt-4", messages=(msg,))
        with pytest.raises(ValueError):
            req.tools = ()  # type: ignore[misc]


class TestChatResponseWithToolCalls:
    def test_without_tool_calls(self) -> None:
        resp = ChatResponse(
            model="gpt-4",
            provider="openai",
            content="hello",
        )
        assert resp.tool_calls is None

    def test_with_tool_calls(self) -> None:
        tc = ToolCall(id="call_1", name="get_weather", arguments={"location": "NYC"})
        resp = ChatResponse(
            model="gpt-4",
            provider="openai",
            content="",
            finish_reason="tool_calls",
            tool_calls=(tc,),
        )
        assert resp.tool_calls is not None
        assert len(resp.tool_calls) == 1
        assert resp.tool_calls[0].name == "get_weather"
        assert resp.tool_calls[0].arguments["location"] == "NYC"

    def test_multiple_tool_calls(self) -> None:
        tc1 = ToolCall(id="c1", name="tool_a")
        tc2 = ToolCall(id="c2", name="tool_b")
        resp = ChatResponse(
            model="gpt-4",
            provider="openai",
            content="",
            finish_reason="tool_calls",
            tool_calls=(tc1, tc2),
        )
        assert len(resp.tool_calls) == 2

    def test_json_round_trip(self) -> None:
        tc = ToolCall(id="c1", name="echo", arguments={"message": "hi"})
        resp = ChatResponse(
            model="gpt-4",
            provider="test",
            content="",
            finish_reason="tool_calls",
            tool_calls=(tc,),
        )
        data = json.loads(resp.model_dump_json())
        assert data["tool_calls"][0]["name"] == "echo"
        assert data["tool_calls"][0]["arguments"]["message"] == "hi"

    def test_frozen_prevents_mutation(self) -> None:
        resp = ChatResponse(model="gpt-4", provider="openai", content="hi")
        with pytest.raises(ValueError):
            resp.tool_calls = ()  # type: ignore[misc]
