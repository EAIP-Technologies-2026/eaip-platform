"""Exception hierarchy for the business calendar service."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class CalendarError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class EventNotFoundError(CalendarError):
    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "CalendarError",
    "EventNotFoundError",
]
