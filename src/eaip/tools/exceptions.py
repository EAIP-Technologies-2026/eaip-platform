"""Tool framework exceptions."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError


class ToolError(EAIPError):
    """Base tool error."""


class ToolNotFoundError(ToolError):
    """Raised when a requested tool is not registered."""

    def __init__(self, name: str) -> None:
        """Initialize with the missing tool name."""
        self.tool_name = name
        super().__init__(f"tool not found: {name!r}")


class ToolExecutionError(ToolError):
    """Raised when a tool's execute method fails."""


__all__ = [
    "ToolError",
    "ToolExecutionError",
    "ToolNotFoundError",
]
