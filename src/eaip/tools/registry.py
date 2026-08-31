"""Tool registry — register, discover, and retrieve tools."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.tools.exceptions import ToolNotFoundError

if TYPE_CHECKING:
    from eaip.tools.base import Tool


class ToolRegistry:
    """A registry for discovering and retrieving tools by name.

    Usage::

        registry = ToolRegistry()
        registry.register(echo_tool)
        tool = registry.get("echo")
        result = await tool.execute(message="hello")
    """

    def __init__(self) -> None:
        """Initialize an empty tool registry."""
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool.

        Args:
            tool: The tool to register.

        Raises:
            ValueError: If a tool with the same name is already registered.
        """
        if tool.name in self._tools:
            raise ValueError(f"tool already registered: {tool.name!r}")
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        """Unregister a tool by name.

        Args:
            name: The tool name.

        Raises:
            ToolNotFoundError: If no tool with that name is registered.
        """
        if name not in self._tools:
            raise ToolNotFoundError(name)
        del self._tools[name]

    def get(self, name: str) -> Tool:
        """Retrieve a tool by name.

        Args:
            name: The tool name.

        Returns:
            The registered tool.

        Raises:
            ToolNotFoundError: If no tool with that name is registered.
        """
        tool = self._tools.get(name)
        if tool is None:
            raise ToolNotFoundError(name)
        return tool

    def try_get(self, name: str) -> Tool | None:
        """Retrieve a tool by name, returning None if not found."""
        return self._tools.get(name)

    def all(self) -> list[Tool]:
        """Return all registered tools."""
        return list(self._tools.values())

    def clear(self) -> None:
        """Remove all registered tools."""
        self._tools.clear()

    def __len__(self) -> int:
        """Return the number of registered tools."""
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        """Check if a tool with the given name is registered."""
        return name in self._tools


__all__ = ["ToolRegistry"]
