"""Runtime module integration for the foundation CLI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.cli.health import CliHealthCheck
from eaip.cli.models import CliConfig, ShellConfig
from eaip.cli.registry import CommandRegistry
from eaip.cli.runner import CommandRunner
from eaip.cli.shell import InteractiveShell
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class CliRuntimeModule:
    """Runtime module that integrates the CLI with the platform kernel."""

    name: str = "cli"

    def __init__(
        self,
        cli_config: CliConfig | None = None,
        shell_config: ShellConfig | None = None,
        registry: CommandRegistry | None = None,
        runner: CommandRunner | None = None,
        shell: InteractiveShell | None = None,
    ) -> None:
        """Initialize the CLI runtime module with optional overrides."""
        self._cli_config = cli_config or CliConfig()
        self._shell_config = shell_config or ShellConfig()
        self._registry = registry or CommandRegistry()
        self._runner = runner or CommandRunner(registry=self._registry)
        self._shell = shell or InteractiveShell(
            registry=self._registry,
            runner=self._runner,
            config=self._shell_config,
        )
        self._health = CliHealthCheck()
        self._log = get_logger("eaip.cli.integration")

    @property
    def registry(self) -> CommandRegistry:
        """Return the command registry."""
        return self._registry

    @property
    def runner(self) -> CommandRunner:
        """Return the command runner."""
        return self._runner

    @property
    def shell(self) -> InteractiveShell:
        """Return the interactive shell."""
        return self._shell

    @property
    def health(self) -> CliHealthCheck:
        """Return the CLI health check."""
        return self._health

    async def start(self, kernel: RuntimeKernel) -> None:
        """Start the CLI module and register with the platform."""
        self._log.info("cli.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.cli",
            title="Foundation CLI",
            description="Foundation CLI and interactive shell with command "
            "registry and argument parsing",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("cli", "shell", "commands"),
        )
        platform.capabilities.register(capability)
        self._health.registered_commands = len(self._registry.list_commands())
        platform.health.register(self._health)
        self._log.info("cli.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:  # noqa: ARG002
        """Stop the CLI module."""
        self._log.info("cli.module.stopping")


__all__ = ["CliRuntimeModule"]
