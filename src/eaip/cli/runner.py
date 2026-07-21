"""Command runner - execute registered commands with timeout and output capture."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from eaip.cli.exceptions import CommandExecutionError, CommandNotFoundError
from eaip.cli.models import CommandResult
from eaip.cli.parser import ArgumentParser, CommandParser
from eaip.cli.registry import CommandRegistry
from eaip.shared.time import utc_now


class CommandRunner:
    """Execute registered commands with timeout and output capture."""

    def __init__(
        self,
        registry: CommandRegistry,
        default_timeout: float = 30.0,
    ) -> None:
        """Initialize the runner with a registry and timeout."""
        self._registry = registry
        self._default_timeout = default_timeout
        self._command_parser = CommandParser()
        self._argument_parser = ArgumentParser()

    @property
    def registry(self) -> CommandRegistry:
        """Return the command registry."""
        return self._registry

    async def execute(
        self,
        command_name: str,
        args: str = "",
        command_timeout: float | None = None,
    ) -> CommandResult:
        """Execute a command by name with optional args and timeout."""
        definition = self._registry.get(command_name)
        if definition is None:
            raise CommandNotFoundError(command_name)

        parsed_args = self._argument_parser.parse(args)
        parsed_args = self._argument_parser.validate(parsed_args, definition)

        handler: Callable[..., Any] | None = self._registry.get_handler(command_name)
        if handler is None:
            raise CommandExecutionError(
                command_name,
                "no handler registered",
            )

        effective_timeout = (
            command_timeout if command_timeout is not None else self._default_timeout
        )
        start = utc_now()

        try:
            result = await asyncio.wait_for(
                handler(**parsed_args),
                timeout=effective_timeout,
            )
            output = str(result) if result is not None else ""
            elapsed = int((utc_now() - start).total_seconds() * 1000)
            return CommandResult(
                success=True,
                output=output,
                duration_ms=elapsed,
            )
        except TimeoutError:
            elapsed = int((utc_now() - start).total_seconds() * 1000)
            return CommandResult(
                success=False,
                output="",
                duration_ms=elapsed,
                error=f"command timed out after {effective_timeout}s",
            )
        except Exception as exc:
            elapsed = int((utc_now() - start).total_seconds() * 1000)
            return CommandResult(
                success=False,
                output="",
                duration_ms=elapsed,
                error=str(exc),
            )


__all__ = ["CommandRunner"]
