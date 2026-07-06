"""Shared testing utilities (importable from any test module)."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime

from eaip.ports.clock import ClockPort


class FrozenClock(ClockPort):
    """A deterministic clock used in tests."""

    def __init__(self, at: datetime | None = None) -> None:
        self._now = at or datetime(2026, 1, 1, tzinfo=UTC)

    def now(self) -> datetime:
        return self._now

    def set(self, at: datetime) -> None:
        self._now = at


@contextmanager
def expect_log_event(_event: str) -> Iterator[None]:
    """Placeholder context manager kept for symmetry with future log assertions."""
    yield
