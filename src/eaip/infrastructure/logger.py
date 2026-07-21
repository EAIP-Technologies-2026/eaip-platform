"""Default :class:`LoggerPort` implementation — in-memory structured logger.

Captures every :class:`LogEntry` in a list for test inspection and provides
a JSON-formatted output for production use.
"""

from __future__ import annotations

import json
import time
from collections.abc import Sequence
from typing import Any

from eaip.ports.logger import LogEntry, LoggerPort

_LOG_LEVELS: dict[str, int] = {
    "CRITICAL": 50,
    "ERROR": 40,
    "WARNING": 30,
    "INFO": 20,
    "DEBUG": 10,
}


class InMemoryLogger(LoggerPort):
    """Captures log entries in-memory and formats them as structured JSON.

    Useful for testing — inspect ``entries`` to assert on logged events.
    """

    def __init__(self, level: str = "INFO", bound_context: dict[str, Any] | None = None) -> None:
        self._level = level.upper()
        self._bound = dict(bound_context) if bound_context else {}
        self._entries: list[LogEntry] = []

    @property
    def entries(self) -> Sequence[LogEntry]:
        return list(self._entries)

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()

    # ── LoggerPort ──────────────────────────────────────────────────────

    def debug(self, event: str, **context: Any) -> None:
        if self.is_enabled_for("DEBUG"):
            self._entries.append(LogEntry("DEBUG", event, {**self._bound, **context}, time.time()))

    def info(self, event: str, **context: Any) -> None:
        if self.is_enabled_for("INFO"):
            self._entries.append(LogEntry("INFO", event, {**self._bound, **context}, time.time()))

    def warning(self, event: str, **context: Any) -> None:
        if self.is_enabled_for("WARNING"):
            self._entries.append(LogEntry("WARNING", event, {**self._bound, **context}, time.time()))

    def error(self, event: str, **context: Any) -> None:
        if self.is_enabled_for("ERROR"):
            self._entries.append(LogEntry("ERROR", event, {**self._bound, **context}, time.time()))

    def critical(self, event: str, **context: Any) -> None:
        if self.is_enabled_for("CRITICAL"):
            self._entries.append(LogEntry("CRITICAL", event, {**self._bound, **context}, time.time()))

    def bind(self, **context: Any) -> LoggerPort:
        merged = {**self._bound, **context}
        return InMemoryLogger(level=self._level, bound_context=merged)

    def is_enabled_for(self, level: str) -> bool:
        return _LOG_LEVELS.get(level.upper(), 0) >= _LOG_LEVELS.get(self._level, 0)

    # ── Output ──────────────────────────────────────────────────────────

    def format_json(self, entry: LogEntry | None = None) -> str:
        """Return a single entry as a JSON line."""
        target = entry or (self._entries[-1] if self._entries else None)
        if target is None:
            return ""
        return json.dumps(target.to_dict(), default=str)

    def format_json_all(self) -> str:
        """Return all entries as newline-delimited JSON (NDJSON)."""
        return "\n".join(self.format_json(e) for e in self._entries)

    def filter_by_level(self, level: str) -> list[LogEntry]:
        return [e for e in self._entries if e.level == level.upper()]

    def filter_by_event(self, event: str) -> list[LogEntry]:
        return [e for e in self._entries if e.event == event]


__all__ = ["InMemoryLogger"]
