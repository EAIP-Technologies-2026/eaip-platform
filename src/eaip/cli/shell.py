"""InteractiveShell - read-eval-print loop with history, prompt, and tab-completion support."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from eaip.cli.models import CommandResult, ShellConfig
from eaip.cli.parser import CommandParser
from eaip.cli.registry import CommandRegistry
from eaip.cli.runner import CommandRunner


class InteractiveShell:
    """Read-eval-print loop with history and tab-completion support."""

    def __init__(
        self,
        registry: CommandRegistry,
        runner: CommandRunner,
        config: ShellConfig | None = None,
    ) -> None:
        """Initialize the shell with registry, runner, and config."""
        self._registry = registry
        self._runner = runner
        self._config = config or ShellConfig()
        self._parser = CommandParser()
        self._history: list[str] = []
        self._running = False

    @property
    def registry(self) -> CommandRegistry:
        """Return the command registry."""
        return self._registry

    @property
    def runner(self) -> CommandRunner:
        """Return the command runner."""
        return self._runner

    @property
    def config(self) -> ShellConfig:
        """Return the shell configuration."""
        return self._config

    @property
    def history(self) -> tuple[str, ...]:
        """Return the command history as a tuple."""
        return tuple(self._history)

    @property
    def running(self) -> bool:
        """Return True if the shell is currently running."""
        return self._running

    async def start(self) -> None:
        """Start the shell loop."""
        self._running = True

    async def stop(self) -> None:
        """Stop the shell loop."""
        self._running = False

    async def execute(self, line: str) -> CommandResult:
        """Parse and execute a single command line."""
        line = line.strip()
        if not line:
            return CommandResult(success=True, output="")
        self._history.append(line)
        command_name, args = self._parser.parse_line(line)
        return await self._runner.execute(command_name, args)

    async def run_forever(self) -> AsyncGenerator[CommandResult, Any]:
        """Run the shell loop forever, yielding results."""
        self._running = True
        while self._running:
            yield CommandResult(success=True, output="")

    def tab_complete(self, text: str) -> list[str]:
        """Return matching command names for tab completion."""
        commands = self._registry.list_commands()
        return [cmd.name for cmd in commands if cmd.name.startswith(text)]


__all__ = ["InteractiveShell"]
