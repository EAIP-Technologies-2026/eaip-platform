"""Domain events for the foundation CLI."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class CliSessionStarted(DomainEvent):
    """Emitted when a CLI session starts."""

    event_type: ClassVar[str] = "eaip.cli.session.started"
    session_id: str = ""


class CliSessionEnded(DomainEvent):
    """Emitted when a CLI session ends."""

    event_type: ClassVar[str] = "eaip.cli.session.ended"
    session_id: str = ""
    command_count: int = 0
    duration_ms: int = 0


class CommandExecuted(DomainEvent):
    """Emitted when a command is executed."""

    event_type: ClassVar[str] = "eaip.cli.command.executed"
    command_name: str = ""
    success: bool = True
    duration_ms: int = 0
    error: str = ""


class ShellCommandRegistered(DomainEvent):
    """Emitted when a command is registered with the shell."""

    event_type: ClassVar[str] = "eaip.cli.shell.command_registered"
    command_name: str = ""
    description: str = ""


CliEvent = CliSessionStarted | CliSessionEnded | CommandExecuted | ShellCommandRegistered


__all__ = [
    "CliEvent",
    "CliSessionEnded",
    "CliSessionStarted",
    "CommandExecuted",
    "ShellCommandRegistered",
]
