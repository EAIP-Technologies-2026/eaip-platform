"""Tests for the Tool protocol and ToolRegistry."""

from __future__ import annotations

import pytest

from eaip.tools.base import Tool
from eaip.tools.exceptions import ToolNotFoundError
from eaip.tools.registry import ToolRegistry


class _SimpleTool:
    """A minimal tool implementation for testing."""

    name = "test_tool"
    description = "A test tool"

    @property
    def parameters(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string"},
            },
            "required": ["input"],
        }

    async def execute(self, **kwargs: object) -> str:
        return f"executed: {kwargs.get('input', '')}"


class TestToolProtocol:
    def test_is_runtime_checkable(self) -> None:
        tool = _SimpleTool()
        assert isinstance(tool, Tool)

    def test_protocol_attributes(self) -> None:
        tool = _SimpleTool()
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"

    def test_parameters_property(self) -> None:
        tool = _SimpleTool()
        params = tool.parameters
        assert params["type"] == "object"
        assert "input" in params["properties"]

    async def test_execute(self) -> None:
        tool = _SimpleTool()
        result = await tool.execute(input="hello")
        assert result == "executed: hello"

    def test_non_tool_is_not_instance(self) -> None:
        assert not isinstance("not a tool", Tool)


class TestToolRegistry:
    @pytest.fixture
    def registry(self) -> ToolRegistry:
        return ToolRegistry()

    @pytest.fixture
    def tool(self) -> _SimpleTool:
        return _SimpleTool()

    def test_register_and_get(self, registry: ToolRegistry, tool: _SimpleTool) -> None:
        registry.register(tool)
        retrieved = registry.get("test_tool")
        assert retrieved is tool

    def test_register_duplicate_raises(self, registry: ToolRegistry, tool: _SimpleTool) -> None:
        registry.register(tool)
        with pytest.raises(ValueError, match="already registered"):
            registry.register(tool)

    def test_get_not_found_raises(self, registry: ToolRegistry) -> None:
        with pytest.raises(ToolNotFoundError, match="tool not found"):
            registry.get("nonexistent")

    def test_try_get_returns_none(self, registry: ToolRegistry) -> None:
        assert registry.try_get("nonexistent") is None

    def test_try_get_returns_tool(self, registry: ToolRegistry, tool: _SimpleTool) -> None:
        registry.register(tool)
        assert registry.try_get("test_tool") is tool

    def test_unregister(self, registry: ToolRegistry, tool: _SimpleTool) -> None:
        registry.register(tool)
        registry.unregister("test_tool")
        assert registry.try_get("test_tool") is None

    def test_unregister_not_found_raises(self, registry: ToolRegistry) -> None:
        with pytest.raises(ToolNotFoundError):
            registry.unregister("nonexistent")

    def test_all_returns_registered_tools(self, registry: ToolRegistry) -> None:
        t1 = _SimpleTool()
        t2 = _SimpleTool()
        t2.name = "tool2"
        registry.register(t1)
        registry.register(t2)
        tools = registry.all()
        assert len(tools) == 2
        assert t1 in tools
        assert t2 in tools

    def test_len(self, registry: ToolRegistry) -> None:
        assert len(registry) == 0
        registry.register(_SimpleTool())
        assert len(registry) == 1

    def test_contains(self, registry: ToolRegistry, tool: _SimpleTool) -> None:
        assert "test_tool" not in registry
        registry.register(tool)
        assert "test_tool" in registry

    def test_clear(self, registry: ToolRegistry) -> None:
        registry.register(_SimpleTool())
        registry.clear()
        assert len(registry) == 0

    def test_register_multiple_tools(self, registry: ToolRegistry) -> None:
        for i in range(5):
            t = _SimpleTool()
            t.name = f"tool_{i}"
            registry.register(t)
        assert len(registry) == 5
