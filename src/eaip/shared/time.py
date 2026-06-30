"""Time and duration utilities.

All timestamps in the platform are UTC and timezone-aware. Wall-clock access
goes through a :class:`Clock` so that tests can supply deterministic time.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Final, Protocol, final, runtime_checkable

UTC: Final = timezone.utc


def utc_now() -> datetime:
    """Return the current wall-clock time as a timezone-aware UTC ``datetime``."""
    return datetime.now(UTC)


@runtime_checkable
class Clock(Protocol):
    """Abstract clock interface — see :mod:`eaip.infrastructure.clock`."""

    def now(self) -> datetime: ...


@final
@dataclass(frozen=True, slots=True, order=True)
class Duration:
    """A non-negative time span, expressed in microseconds.

    ``Duration`` is intentionally immutable, hashable, and orderable so that
    it can be used as a dictionary key, set element, or sort key.
    """

    microseconds: int

    def __post_init__(self) -> None:
        if self.microseconds < 0:
            raise ValueError("Duration must be non-negative")

    @classmethod
    def from_seconds(cls, seconds: float) -> "Duration":
        return cls(int(round(seconds * 1_000_000)))

    @classmethod
    def from_milliseconds(cls, ms: float) -> "Duration":
        return cls(int(round(ms * 1_000)))

    @classmethod
    def from_timedelta(cls, td: timedelta) -> "Duration":
        return cls(int(td.total_seconds() * 1_000_000))

    @property
    def seconds(self) -> float:
        return self.microseconds / 1_000_000

    def to_timedelta(self) -> timedelta:
        return timedelta(microseconds=self.microseconds)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.seconds:.6f}s"


#: Callable shape for time providers (compatible with :class:`Clock`).
TimeProvider = Callable[[], datetime]

__all__ = ["Clock", "Duration", "TimeProvider", "UTC", "utc_now"]
