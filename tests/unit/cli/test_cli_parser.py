"""Tests for CommandParser and ArgumentParser."""

from __future__ import annotations

import pytest

from eaip.cli.exceptions import InvalidArgumentError
from eaip.cli.models import CommandArg, CommandDefinition
from eaip.cli.parser import ArgumentParser, CommandParser


class TestArgumentParser:
    def test_empty_args(self) -> None:
        parser = ArgumentParser()
        result = parser.parse("")
        assert result == {}

    def test_named_args(self) -> None:
        parser = ArgumentParser()
        result = parser.parse("--env prod --verbose")
        assert result == {"env": "prod", "verbose": True}

    def test_short_args(self) -> None:
        parser = ArgumentParser()
        result = parser.parse("-e prod -v")
        assert result == {"e": "prod", "v": True}

    def test_equals_style(self) -> None:
        parser = ArgumentParser()
        result = parser.parse("--env=prod --count=3")
        assert result == {"env": "prod", "count": "3"}

    def test_quoted_args(self) -> None:
        parser = ArgumentParser()
        result = parser.parse('--name "hello world"')
        assert result == {"name": "hello world"}

    def test_validate_required(self) -> None:
        parser = ArgumentParser()
        definition = CommandDefinition(
            name="test",
            arguments=(CommandArg(name="env", required=True),),
        )
        with pytest.raises(InvalidArgumentError):
            parser.validate({}, definition)

    def test_validate_optional(self) -> None:
        parser = ArgumentParser()
        definition = CommandDefinition(
            name="test",
            arguments=(CommandArg(name="env", required=False),),
        )
        result = parser.validate({}, definition)
        assert result == {}


class TestCommandParser:
    def test_empty_line(self) -> None:
        parser = CommandParser()
        cmd, args = parser.parse_line("")
        assert cmd == ""
        assert args == ""

    def test_blank_line(self) -> None:
        parser = CommandParser()
        cmd, args = parser.parse_line("   ")
        assert cmd == ""
        assert args == ""

    def test_command_only(self) -> None:
        parser = CommandParser()
        cmd, args = parser.parse_line("deploy")
        assert cmd == "deploy"
        assert args == ""

    def test_command_with_args(self) -> None:
        parser = CommandParser()
        cmd, args = parser.parse_line("deploy --env prod --verbose")
        assert cmd == "deploy"
        assert args == "--env prod --verbose"

    def test_command_with_quoted_args(self) -> None:
        parser = CommandParser()
        cmd, args = parser.parse_line('say "hello world"')
        assert cmd == "say"
        assert args == "hello world"

    def test_resolve(self) -> None:
        parser = CommandParser()
        definition = CommandDefinition(name="deploy")
        registry = {definition.name: definition}
        result = parser.resolve("deploy", registry)
        assert result is definition

    def test_resolve_not_found(self) -> None:
        parser = CommandParser()
        result = parser.resolve("unknown", {})
        assert result is None
