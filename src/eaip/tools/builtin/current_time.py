"""CurrentTimeTool — returns the current UTC time."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic.json_schema import JsonSchemaValue


class CurrentTimeTool:
    """A tool that returns the current UTC date and time.

    Accepts an optional timezone offset format parameter.
    """

    name = "current_time"
    description = "Get the current UTC date and time."

    @property
    def parameters(self) -> JsonSchemaValue:
        """JSON Schema for the format parameter."""
        return {
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "description": (
                        "Optional strftime format string (default: '%Y-%m-%dT%H:%M:%SZ')."
                    ),
                    "default": "%Y-%m-%dT%H:%M:%SZ",
                },
            },
        }

    async def execute(self, **kwargs: object) -> str:
        """Return the current UTC time formatted per the optional format string."""
        fmt = str(kwargs.get("format", "%Y-%m-%dT%H:%M:%SZ"))
        return datetime.now(UTC).strftime(fmt)


__all__ = ["CurrentTimeTool"]
