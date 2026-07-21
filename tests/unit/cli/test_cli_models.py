"""Tests for CLI domain models."""

from __future__ import annotations

from datetime import datetime

import pytest

from eaip.cli.models import (
    CliConfig,
    CliSession,
    CommandArg,
    CommandDefinition,
    CommandResult,
    ShellConfig,
)


class TestCommandArg:
    def test_required_fields(self) -> None:
        arg = CommandArg(name="path")
        assert arg.name == "path"
        assert arg.type == "str"
        assert arg.description == ""
        assert arg.required is True
        assert arg.default is None

    def test_with_all_fields(self) -> None:
        arg = CommandArg(
            name="verbose",
            type="bool",
            description="Enable verbose output",
            required=False,
            default=False,
        )
        assert arg.name == "verbose"
        assert arg.type == "bool"
        assert arg.description == "Enable verbose output"
        assert arg.required is False
        assert arg.default is False

    def test_frozen(self) -> None:
        arg = CommandArg(name="path")
        with pytest.raises(ValueError):
            arg.name = "changed"  # type: ignore[misc]


class TestCommandDefinition:
    def test_required_fields(self) -> None:
        cmd = CommandDefinition(name="deploy")
        assert cmd.name == "deploy"
        assert cmd.description == ""
        assert cmd.arguments == ()

    def test_with_all_fields(self) -> None:
        args = (
            CommandArg(name="env", description="Environment"),
            CommandArg(name="verbose", required=False, default=False),
        )
        cmd = CommandDefinition(
            name="deploy",
            description="Deploy to environment",
            arguments=args,
        )
        assert cmd.name == "deploy"
        assert cmd.description == "Deploy to environment"
        assert len(cmd.arguments) == 2

    def test_frozen(self) -> None:
        cmd = CommandDefinition(name="deploy")
        with pytest.raises(ValueError):
            cmd.name = "rollback"  # type: ignore[misc]


class TestCommandResult:
    def test_required_fields(self) -> None:
        result = CommandResult(success=True)
        assert result.success is True
        assert result.output == ""
        assert result.duration_ms == 0
        assert result.error is None

    def test_failure_result(self) -> None:
        result = CommandResult(
            success=False,
            output="",
            duration_ms=150,
            error="something went wrong",
        )
        assert result.success is False
        assert result.duration_ms == 150
        assert result.error == "something went wrong"

    def test_frozen(self) -> None:
        result = CommandResult(success=True)
        with pytest.raises(ValueError):
            result.success = False  # type: ignore[misc]


class TestCliConfig:
    def test_defaults(self) -> None:
        config = CliConfig()
        assert config.prompt_style == "default"
        assert config.history_size == 1000
        assert config.colors_enabled is True
        assert config.default_timeout == 30.0

    def test_custom(self) -> None:
        config = CliConfig(
            prompt_style="minimal",
            history_size=500,
            colors_enabled=False,
            default_timeout=60.0,
        )
        assert config.prompt_style == "minimal"
        assert config.history_size == 500
        assert config.colors_enabled is False
        assert config.default_timeout == 60.0

    def test_frozen(self) -> None:
        config = CliConfig()
        with pytest.raises(ValueError):
            config.history_size = 2000  # type: ignore[misc]


class TestShellConfig:
    def test_defaults(self) -> None:
        config = ShellConfig()
        assert config.prompt_template == "> "
        assert config.welcome_message == "EAIP Interactive Shell"
        assert config.history_file == ".eaip_history"

    def test_custom(self) -> None:
        config = ShellConfig(
            prompt_template="$ ",
            welcome_message="Welcome",
            history_file="/tmp/history",
        )
        assert config.prompt_template == "$ "
        assert config.welcome_message == "Welcome"
        assert config.history_file == "/tmp/history"

    def test_frozen(self) -> None:
        config = ShellConfig()
        with pytest.raises(ValueError):
            config.prompt_template = "# "  # type: ignore[misc]


class TestCliSession:
    def test_required_fields(self) -> None:
        session = CliSession(session_id="sess_1")
        assert session.session_id == "sess_1"
        assert isinstance(session.start_time, datetime)
        assert session.command_count == 0
        assert session.history == ()

    def test_with_history(self) -> None:
        results = (
            CommandResult(success=True, output="ok"),
            CommandResult(success=False, error="fail"),
        )
        session = CliSession(
            session_id="sess_2",
            command_count=2,
            history=results,
        )
        assert session.command_count == 2
        assert len(session.history) == 2
        assert session.history[0].output == "ok"
        assert session.history[1].error == "fail"

    def test_frozen(self) -> None:
        session = CliSession(session_id="sess_1")
        with pytest.raises(ValueError):
            session.command_count = 10  # type: ignore[misc]
