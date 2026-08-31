"""Tests for CLI exceptions."""

from __future__ import annotations

from eaip.cli.exceptions import (
    CliError,
    CommandExecutionError,
    CommandNotFoundError,
    InvalidArgumentError,
)
from eaip.exceptions.base import EAIPError, ErrorCode


class TestCliError:
    def test_is_eaip_error(self) -> None:
        assert issubclass(CliError, EAIPError)

    def test_default_code(self) -> None:
        err = CliError("generic error")
        assert err.code is ErrorCode.UNKNOWN


class TestCommandNotFoundError:
    def test_message(self) -> None:
        err = CommandNotFoundError("deploy")
        assert "deploy" in str(err)
        assert err.command_name == "deploy"
        assert err.code is ErrorCode.NOT_FOUND

    def test_is_cli_error(self) -> None:
        assert issubclass(CommandNotFoundError, CliError)


class TestCommandExecutionError:
    def test_message(self) -> None:
        err = CommandExecutionError("deploy", "permission denied")
        assert "deploy" in str(err)
        assert "permission denied" in str(err)
        assert err.command_name == "deploy"
        assert err.code is ErrorCode.INTERNAL_ERROR

    def test_is_cli_error(self) -> None:
        assert issubclass(CommandExecutionError, CliError)


class TestInvalidArgumentError:
    def test_message(self) -> None:
        err = InvalidArgumentError("env", "invalid value")
        assert "env" in str(err)
        assert "invalid value" in str(err)
        assert err.arg_name == "env"
        assert err.code is ErrorCode.VALIDATION_FAILED

    def test_is_cli_error(self) -> None:
        assert issubclass(InvalidArgumentError, CliError)
