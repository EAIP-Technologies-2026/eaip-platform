"""Tests for CliRuntimeModule."""

from __future__ import annotations

from unittest.mock import MagicMock

from eaip.cli.health import CliHealthCheck
from eaip.cli.integration import CliRuntimeModule
from eaip.cli.models import CliConfig, ShellConfig
from eaip.cli.registry import CommandRegistry
from eaip.cli.runner import CommandRunner
from eaip.cli.shell import InteractiveShell


class TestCliRuntimeModule:
    def test_default_construction(self) -> None:
        module = CliRuntimeModule()
        assert module.name == "cli"
        assert isinstance(module.registry, CommandRegistry)
        assert isinstance(module.runner, CommandRunner)
        assert isinstance(module.shell, InteractiveShell)
        assert isinstance(module.health, CliHealthCheck)

    def test_custom_construction(self) -> None:
        cli_config = CliConfig(history_size=500)
        shell_config = ShellConfig(prompt_template="$ ")
        registry = CommandRegistry()
        runner = CommandRunner(registry=registry)
        shell = InteractiveShell(registry=registry, runner=runner)
        module = CliRuntimeModule(
            cli_config=cli_config,
            shell_config=shell_config,
            registry=registry,
            runner=runner,
            shell=shell,
        )
        assert module.registry is registry
        assert module.runner is runner
        assert module.shell is shell

    async def test_start_registers_capability(self) -> None:
        module = CliRuntimeModule()
        kernel = MagicMock()
        kernel.platform = MagicMock()
        kernel.platform.capabilities = MagicMock()
        kernel.platform.health = MagicMock()

        await module.start(kernel)

        kernel.platform.capabilities.register.assert_called_once()
        kernel.platform.health.register.assert_called_once()

    async def test_start_registers_health_check(self) -> None:
        module = CliRuntimeModule()
        kernel = MagicMock()
        kernel.platform = MagicMock()
        kernel.platform.capabilities = MagicMock()
        kernel.platform.health = MagicMock()

        await module.start(kernel)

        call_args = kernel.platform.health.register.call_args
        registered = call_args[0][0]
        assert isinstance(registered, CliHealthCheck)

    async def test_stop(self) -> None:
        module = CliRuntimeModule()
        kernel = MagicMock()
        await module.stop(kernel)

    def test_properties(self) -> None:
        module = CliRuntimeModule()
        assert isinstance(module.registry, CommandRegistry)
        assert isinstance(module.runner, CommandRunner)
        assert isinstance(module.shell, InteractiveShell)
        assert isinstance(module.health, CliHealthCheck)

    async def test_start_with_capability_tags(self) -> None:
        module = CliRuntimeModule()
        kernel = MagicMock()
        kernel.platform = MagicMock()
        kernel.platform.capabilities = MagicMock()
        kernel.platform.health = MagicMock()

        await module.start(kernel)

        call_args = kernel.platform.capabilities.register.call_args
        capability = call_args[0][0]
        assert capability.name == "eaip.cli"
        assert "cli" in capability.tags
        assert "shell" in capability.tags
        assert "commands" in capability.tags
