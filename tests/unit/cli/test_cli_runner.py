"""Tests for CommandRunner."""

from __future__ import annotations

import asyncio

import pytest

from eaip.cli.exceptions import CommandNotFoundError
from eaip.cli.models import CommandDefinition
from eaip.cli.registry import CommandRegistry
from eaip.cli.runner import CommandRunner


class TestCommandRunner:
    @pytest.fixture
    def registry(self) -> CommandRegistry:
        reg = CommandRegistry()

        async def greet(**kwargs: str) -> str:
            name = kwargs.get("name", "world")
            return f"hello {name}"

        async def slow() -> str:
            await asyncio.sleep(10)
            return "done"

        reg.register(
            CommandDefinition(name="greet", arguments=()),
            handler=greet,
        )
        reg.register(
            CommandDefinition(name="fail"),
            handler=lambda: (_ for _ in ()).throw(  # type: ignore[return-value]
                RuntimeError("oops"),
            ),
        )
        reg.register(
            CommandDefinition(name="slow", arguments=()),
            handler=slow,
        )
        return reg

    @pytest.fixture
    def runner(self, registry: CommandRegistry) -> CommandRunner:
        return CommandRunner(registry=registry, default_timeout=5.0)

    async def test_execute_success(self, runner: CommandRunner) -> None:
        result = await runner.execute("greet")
        assert result.success is True
        assert "hello" in result.output
        assert result.error is None

    async def test_execute_not_found(self, runner: CommandRunner) -> None:
        with pytest.raises(CommandNotFoundError):
            await runner.execute("unknown")

    async def test_execute_failure(self, runner: CommandRunner) -> None:
        result = await runner.execute("fail")
        assert result.success is False
        assert result.error is not None
        assert "oops" in result.error

    async def test_execute_timeout(self, runner: CommandRunner) -> None:
        result = await runner.execute("slow", command_timeout=0.01)
        assert result.success is False
        assert result.error is not None
        assert "timed out" in result.error
        assert result.duration_ms > 0

    async def test_execute_with_args(self, runner: CommandRunner) -> None:
        result = await runner.execute("greet", args="--name alice")
        assert result.success is True
        assert "hello alice" in result.output
