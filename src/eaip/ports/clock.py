"""Clock port — abstracts wall-clock access."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class ClockPort(Protocol):
    """Anything that can answer "what time is it (UTC)?"."""

    def now(self) -> datetime:
        """Returns the current UTC time.

        Returns:
            The current UTC time.
        """
        ...


__all__ = ["ClockPort"]
