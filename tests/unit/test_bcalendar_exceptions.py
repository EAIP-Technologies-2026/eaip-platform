"""Tests for bcalendar exceptions."""

from __future__ import annotations

from eaip.bcalendar.exceptions import CalendarError, EventNotFoundError
from eaip.exceptions.base import EAIPError, ErrorCode


class TestCalendarError:
    def test_base_exception(self) -> None:
        err = CalendarError("Calendar error")
        assert isinstance(err, EAIPError)
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestEventNotFoundError:
    def test_default_code(self) -> None:
        err = EventNotFoundError("Not found")
        assert isinstance(err, CalendarError)
        assert err.code == ErrorCode.NOT_FOUND

    def test_custom_message(self) -> None:
        err = EventNotFoundError("Event 'e1' not found")
        assert "e1" in str(err)
