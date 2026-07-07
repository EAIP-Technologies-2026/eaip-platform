"""Default :class:`ClockPort` implementation backed by the system clock."""

from __future__ import annotations

from datetime import datetime

from eaip.ports.clock import ClockPort
from eaip.shared.time import utc_now


class SystemClock(ClockPort):
    """Wall-clock implementation returning timezone-aware UTC datetimes."""

    def now(self) -> datetime:
        """Returns the current UTC time.

        Returns:
            The current timezone-aware UTC datetime.
        """
        return utc_now()


__all__ = ["SystemClock"]
