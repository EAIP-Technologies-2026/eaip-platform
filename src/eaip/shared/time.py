"""Time and duration utilities.

All timestamps in the platform are UTC and timezone-aware. Wall-clock access
goes through a :class:`Clock` so that tests can supply deterministic time.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol, Self, final, runtime_checkable


def utc_now() -> datetime:
    """Return the current wall-clock time as a timezone-aware UTC ``datetime``."""
    return datetime.now(UTC)


@runtime_checkable
class Clock(Protocol):
    """Abstract clock interface — see :mod:`eaip.infrastructure.clock`."""

    def now(self: Self) -> datetime:
        """Return the current time."""
        ...


@final
@dataclass(frozen=True, slots=True, order=True)
class Duration:
    """A non-negative time span, expressed in microseconds.

    ``Duration`` is intentionally immutable, hashable, and orderable so that
    it can be used as a dictionary key, set element, or sort key.
    """

    microseconds: int

    def __post_init__(self: Self) -> None:
        """Validate that the duration is non-negative."""
        if self.microseconds < 0:
            raise ValueError("Duration must be non-negative")

    @classmethod
    def from_seconds(cls: type[Self], seconds: float) -> Self:
        """Create a Duration from seconds."""
        return cls(round(seconds * 1_000_000))

    @classmethod
    def from_milliseconds(cls: type[Self], ms: float) -> Self:
        """Create a Duration from milliseconds."""
        return cls(round(ms * 1_000))

    @classmethod
    def from_timedelta(cls: type[Self], td: timedelta) -> Self:
        """Create a Duration from a timedelta."""
        return cls(int(td.total_seconds() * 1_000_000))

    @property
    def seconds(self: Self) -> float:
        """Return the duration in seconds."""
        return self.microseconds / 1_000_000

    def to_timedelta(self: Self) -> timedelta:
        """Convert to a timedelta."""
        return timedelta(microseconds=self.microseconds)

    def __str__(self: Self) -> str:  # pragma: no cover - trivial
        """Return the string representation."""
        return f"{self.seconds:.6f}s"


#: Callable shape for time providers (compatible with :class:`Clock`).
TimeProvider = Callable[[], datetime]

__all__ = ["UTC", "Clock", "Duration", "TimeProvider", "utc_now"]
