"""Tool protocol — the abstract interface for executable tools."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic.json_schema import JsonSchemaValue


@runtime_checkable
class Tool(Protocol):
    """Protocol for executable tools that LLMs can invoke.

    Implementations must provide:
    - name: A unique tool name (used by the LLM to select this tool).
    - description: A human-readable description of what the tool does.
    - parameters: A JSON Schema dict describing the expected arguments.
    - execute(): Execute the tool with the given arguments and return a string result.
    """

    name: str
    description: str

    @property
    def parameters(self) -> JsonSchemaValue:
        """Return a JSON Schema describing the tool's input parameters.

        The schema is used by the LLM to generate correctly-shaped arguments.
        """
        ...

    async def execute(self, **kwargs: object) -> str:
        """Execute the tool with the provided keyword arguments.

        Args:
            **kwargs: Arguments matching the tool's parameter schema.

        Returns:
            The tool output as a string.
        """
        ...


__all__ = ["Tool"]
