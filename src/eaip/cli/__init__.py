"""Foundation CLI - interactive shell, command registry, and argument parsing."""

from __future__ import annotations

from eaip.cli.events import (
    CliEvent,
    CliSessionEnded,
    CliSessionStarted,
    CommandExecuted,
    ShellCommandRegistered,
)
from eaip.cli.exceptions import (
    CliError,
    CommandExecutionError,
    CommandNotFoundError,
    InvalidArgumentError,
)
from eaip.cli.health import CliHealthCheck
from eaip.cli.integration import CliRuntimeModule
from eaip.cli.models import (
    CliConfig,
    CliSession,
    CommandArg,
    CommandDefinition,
    CommandResult,
    ShellConfig,
)
from eaip.cli.parser import ArgumentParser, CommandParser
from eaip.cli.registry import CommandRegistry
from eaip.cli.runner import CommandRunner
from eaip.cli.shell import InteractiveShell

__all__ = [
    "ArgumentParser",
    "CliConfig",
    "CliError",
    "CliEvent",
    "CliHealthCheck",
    "CliRuntimeModule",
    "CliSession",
    "CliSessionEnded",
    "CliSessionStarted",
    "CommandArg",
    "CommandDefinition",
    "CommandExecuted",
    "CommandExecutionError",
    "CommandNotFoundError",
    "CommandParser",
    "CommandRegistry",
    "CommandResult",
    "CommandRunner",
    "InteractiveShell",
    "InvalidArgumentError",
    "ShellCommandRegistered",
    "ShellConfig",
]
