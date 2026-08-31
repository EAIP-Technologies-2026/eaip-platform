"""Logger port — abstract logging interface for the platform.

The :class:`LoggerPort` protocol decouples platform services from any specific
logging framework (structlog, stdlib logging, OpenTelemetry, etc.).

Implementations must support structured key-value pairs and standard log levels.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LoggerPort(Protocol):
    """Pluggable structured logger contract."""

    def debug(self, event: str, **context: Any) -> None: ...
    def info(self, event: str, **context: Any) -> None: ...
    def warning(self, event: str, **context: Any) -> None: ...
    def error(self, event: str, **context: Any) -> None: ...
    def critical(self, event: str, **context: Any) -> None: ...

    def bind(self, **context: Any) -> LoggerPort:
        """Return a new logger with *context* bound permanently."""
        ...

    def is_enabled_for(self, level: str) -> bool:
        """Return ``True`` if *level* (``"DEBUG"``, ``"INFO"``, …) is enabled."""
        ...


class LogEntry:
    """A single structured log entry captured by :class:`InMemoryLogger`."""

    __slots__ = ("context", "event", "level", "timestamp")

    def __init__(
        self,
        level: str,
        event: str,
        context: Mapping[str, Any] | None = None,
        timestamp: float | None = None,
    ) -> None:
        self.level = level
        self.event = event
        self.context = dict(context) if context else {}
        self.timestamp = timestamp or 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "event": self.event,
            "context": self.context,
            "timestamp": self.timestamp,
        }


__all__ = ["LogEntry", "LoggerPort"]
