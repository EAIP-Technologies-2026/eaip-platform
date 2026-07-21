"""Exception hierarchy for the foundation CLI."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class CliError(EAIPError):
    """Base exception for all CLI errors."""

    default_code = ErrorCode.UNKNOWN
    default_severity = ErrorSeverity.ERROR


class CommandNotFoundError(CliError):
    """Raised when a requested command is not found."""

    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING

    def __init__(self, command_name: str) -> None:
        """Initialize with the missing command name."""
        self.command_name = command_name
        super().__init__(f"command not found: {command_name!r}")


class CommandExecutionError(CliError):
    """Raised when command execution fails."""

    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR

    def __init__(self, command_name: str, message: str) -> None:
        """Initialize with command name and error message."""
        self.command_name = command_name
        super().__init__(f"execution failed for {command_name!r}: {message}")


class InvalidArgumentError(CliError):
    """Raised when a command argument is invalid."""

    default_code = ErrorCode.VALIDATION_FAILED
    default_severity = ErrorSeverity.WARNING

    def __init__(self, arg_name: str, message: str) -> None:
        """Initialize with argument name and error message."""
        self.arg_name = arg_name
        super().__init__(f"invalid argument {arg_name!r}: {message}")


__all__ = [
    "CliError",
    "CommandExecutionError",
    "CommandNotFoundError",
    "InvalidArgumentError",
]
