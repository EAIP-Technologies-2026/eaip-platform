"""Command and argument parsers for the foundation CLI."""

from __future__ import annotations

import shlex
from typing import Any, cast

from eaip.cli.exceptions import InvalidArgumentError
from eaip.cli.models import CommandDefinition

_SHORT_FLAG_LENGTH = 2


class ArgumentParser:
    """Parse argument strings into key-value pairs."""

    def parse(self, args: str) -> dict[str, Any]:
        """Parse a raw argument string into a key-value dictionary."""
        result: dict[str, Any] = {}
        tokens = shlex.split(args)
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token.startswith("--"):
                key = token[2:]
                if "=" in key:
                    k, v = key.split("=", 1)
                    result[k] = v
                elif i + 1 < len(tokens) and not tokens[i + 1].startswith("--"):
                    i += 1
                    result[key] = tokens[i]
                else:
                    result[key] = True
            elif token.startswith("-") and len(token) == _SHORT_FLAG_LENGTH:
                key = token[1:]
                if i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
                    i += 1
                    result[key] = tokens[i]
                else:
                    result[key] = True
            i += 1
        return result

    def validate(
        self,
        parsed: dict[str, Any],
        definition: CommandDefinition,
    ) -> dict[str, Any]:
        """Validate parsed arguments against a command definition."""
        for arg in definition.arguments:
            if arg.required and arg.name not in parsed:
                raise InvalidArgumentError(
                    arg.name,
                    f"required argument --{arg.name} is missing",
                )
        return parsed


class CommandParser:
    """Parse raw text commands into structured CommandDefinition lookups."""

    def parse_line(self, line: str) -> tuple[str, str]:
        """Parse a raw input line into command name and argument string."""
        parts = shlex.split(line.strip())
        if not parts:
            return ("", "")
        command = parts[0]
        args = " ".join(parts[1:]) if len(parts) > 1 else ""
        return (command, args)

    def resolve(
        self,
        command_name: str,
        registry: Any,
    ) -> CommandDefinition | None:
        """Resolve a command name to its definition from a registry."""
        return cast("CommandDefinition | None", registry.get(command_name))


__all__ = ["ArgumentParser", "CommandParser"]
