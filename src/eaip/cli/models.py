"""CLI domain models - CliConfig, CommandDefinition, CommandArg, CommandResult, and more."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class CommandArg(BaseModel):
    """A single argument for a CLI command."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    type: str = "str"
    description: str = ""
    required: bool = True
    default: Any = None


class CommandDefinition(BaseModel):
    """Definition of a CLI command with its arguments."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    description: str = ""
    arguments: tuple[CommandArg, ...] = Field(default_factory=tuple)


class CommandResult(BaseModel):
    """Result of executing a CLI command."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    success: bool
    output: str = ""
    duration_ms: int = 0
    error: str | None = None


class CliConfig(BaseModel):
    """Configuration for the CLI system."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    prompt_style: str = "default"
    history_size: int = 1000
    colors_enabled: bool = True
    default_timeout: float = 30.0


class ShellConfig(BaseModel):
    """Configuration for the interactive shell."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    prompt_template: str = "> "
    welcome_message: str = "EAIP Interactive Shell"
    history_file: str = ".eaip_history"


class CliSession(BaseModel):
    """A CLI session with history and command count."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    session_id: str
    start_time: datetime = Field(default_factory=utc_now)
    command_count: int = 0
    history: tuple[CommandResult, ...] = Field(default_factory=tuple)


__all__ = [
    "CliConfig",
    "CliSession",
    "CommandArg",
    "CommandDefinition",
    "CommandResult",
    "ShellConfig",
]
