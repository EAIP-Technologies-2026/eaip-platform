"""EchoTool — echoes back the input message."""

from __future__ import annotations

from pydantic.json_schema import JsonSchemaValue


class EchoTool:
    """A tool that echoes back the input message.

    Useful for testing tool-calling pipelines.
    """

    name = "echo"
    description = "Echoes back the input message. Use for testing."

    @property
    def parameters(self) -> JsonSchemaValue:
        """JSON Schema for the message parameter."""
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The message to echo back.",
                },
            },
            "required": ["message"],
        }

    async def execute(self, **kwargs: object) -> str:
        """Return the input message prefixed with 'echo: '."""
        message = kwargs.get("message", "")
        return f"echo: {message}"


__all__ = ["EchoTool"]
