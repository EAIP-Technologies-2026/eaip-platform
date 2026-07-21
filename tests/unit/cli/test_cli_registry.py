"""Tests for CommandRegistry."""

from __future__ import annotations

from eaip.cli.models import CommandDefinition
from eaip.cli.registry import CommandRegistry


class TestCommandRegistry:
    def test_register_and_get(self) -> None:
        registry = CommandRegistry()
        definition = CommandDefinition(name="deploy")
        registry.register(definition)
        assert registry.get("deploy") is definition

    def test_get_nonexistent(self) -> None:
        registry = CommandRegistry()
        assert registry.get("unknown") is None

    def test_register_with_handler(self) -> None:
        registry = CommandRegistry()

        def handler() -> str:
            return "ok"

        definition = CommandDefinition(name="deploy")
        registry.register(definition, handler=handler)
        assert registry.get_handler("deploy") is handler

    def test_get_handler_nonexistent(self) -> None:
        registry = CommandRegistry()
        assert registry.get_handler("unknown") is None

    def test_unregister(self) -> None:
        registry = CommandRegistry()
        definition = CommandDefinition(name="deploy")
        registry.register(definition)
        assert registry.has_command("deploy") is True
        registry.unregister("deploy")
        assert registry.has_command("deploy") is False
        assert registry.get("deploy") is None

    def test_list_commands(self) -> None:
        registry = CommandRegistry()
        cmd1 = CommandDefinition(name="deploy")
        cmd2 = CommandDefinition(name="rollback")
        registry.register(cmd1)
        registry.register(cmd2)
        commands = registry.list_commands()
        assert len(commands) == 2
        assert cmd1 in commands
        assert cmd2 in commands

    def test_has_command(self) -> None:
        registry = CommandRegistry()
        registry.register(CommandDefinition(name="deploy"))
        assert registry.has_command("deploy") is True
        assert registry.has_command("unknown") is False

    def test_unregister_nonexistent(self) -> None:
        registry = CommandRegistry()
        registry.unregister("unknown")
        assert True
