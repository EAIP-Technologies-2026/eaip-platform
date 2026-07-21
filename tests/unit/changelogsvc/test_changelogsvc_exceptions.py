"""Tests for change log service exception hierarchy."""

from __future__ import annotations

from eaip.changelogsvc.exceptions import ChangeLogError
from eaip.exceptions.base import EAIPError, ErrorCode


class TestChangeLogError:
    def test_is_eaip_error(self) -> None:
        err = ChangeLogError("generic error")
        assert isinstance(err, EAIPError)

    def test_default_code(self) -> None:
        err = ChangeLogError("test")
        assert err.code == ErrorCode.UNKNOWN

    def test_message(self) -> None:
        err = ChangeLogError("something went wrong")
        assert str(err) == "something went wrong"
