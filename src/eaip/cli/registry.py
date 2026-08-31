"""CommandRegistry - register, unregister, list, and get commands."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from eaip.cli.models import CommandDefinition


class CommandRegistry:
    """Observable registry for CLI commands."""

    def __init__(self) -> None:
        """Initialize an empty command registry."""
        self._commands: dict[str, CommandDefinition] = {}
        self._handlers: dict[str, Callable[..., Any]] = {}

    def register(
        self,
        definition: CommandDefinition,
        handler: Callable[..., Any] | None = None,
    ) -> None:
        """Register a command definition with an optional handler."""
        self._commands[definition.name] = definition
        if handler is not None:
            self._handlers[definition.name] = handler

    def unregister(self, command_name: str) -> None:
        """Unregister a command and its handler by name."""
        self._commands.pop(command_name, None)
        self._handlers.pop(command_name, None)

    def get(self, command_name: str) -> CommandDefinition | None:
        """Get a command definition by name, or None if not found."""
        return self._commands.get(command_name)

    def get_handler(self, command_name: str) -> Callable[..., Any] | None:
        """Get a command handler by name, or None if not found."""
        return self._handlers.get(command_name)

    def list_commands(self) -> list[CommandDefinition]:
        """Return all registered command definitions."""
        return list(self._commands.values())

    def has_command(self, command_name: str) -> bool:
        """Return True if a command is registered by name."""
        return command_name in self._commands


__all__ = ["CommandRegistry"]
