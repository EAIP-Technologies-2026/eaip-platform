"""Tests for InteractiveShell."""

from __future__ import annotations

import pytest

from eaip.cli.models import CommandDefinition, ShellConfig
from eaip.cli.registry import CommandRegistry
from eaip.cli.runner import CommandRunner
from eaip.cli.shell import InteractiveShell


class TestInteractiveShell:
    @pytest.fixture
    def registry(self) -> CommandRegistry:
        reg = CommandRegistry()

        async def greet(**kwargs: str) -> str:
            name = kwargs.get("name", "world")
            return f"hello {name}"

        reg.register(
            CommandDefinition(name="greet", arguments=()),
            handler=greet,
        )
        return reg

    @pytest.fixture
    def shell(self, registry: CommandRegistry) -> InteractiveShell:
        runner = CommandRunner(registry=registry)
        return InteractiveShell(
            registry=registry,
            runner=runner,
            config=ShellConfig(prompt_template="$ "),
        )

    async def test_execute(self, shell: InteractiveShell) -> None:
        result = await shell.execute("greet")
        assert result.success is True
        assert "hello" in result.output

    async def test_execute_with_args(self, shell: InteractiveShell) -> None:
        result = await shell.execute('greet --name "alice"')
        assert result.success is True
        assert "hello alice" in result.output

    async def test_execute_blank_line(self, shell: InteractiveShell) -> None:
        result = await shell.execute("")
        assert result.success is True
        assert result.output == ""

    async def test_execute_whitespace(self, shell: InteractiveShell) -> None:
        result = await shell.execute("   ")
        assert result.success is True
        assert result.output == ""

    async def test_history(self, shell: InteractiveShell) -> None:
        await shell.execute("greet")
        await shell.execute("greet --name bob")
        assert len(shell.history) == 2
        assert shell.history[0] == "greet"
        assert shell.history[1] == "greet --name bob"

    async def test_start_stop(self, shell: InteractiveShell) -> None:
        assert shell.running is False
        await shell.start()
        assert shell.running is True
        await shell.stop()
        assert shell.running is False

    def test_tab_complete(self, shell: InteractiveShell) -> None:
        matches = shell.tab_complete("gr")
        assert "greet" in matches

    def test_tab_complete_no_match(self, shell: InteractiveShell) -> None:
        matches = shell.tab_complete("zzz")
        assert matches == []

    def test_config(self, shell: InteractiveShell) -> None:
        assert shell.config.prompt_template == "$ "

    def test_properties(self, shell: InteractiveShell) -> None:
        assert shell.registry is not None
        assert shell.runner is not None
