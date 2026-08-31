"""Tests for :mod:`eaip.fileintmon.exceptions`."""

from __future__ import annotations

from eaip.exceptions.base import ErrorCode
from eaip.fileintmon.exceptions import FileNotFoundError, IntegrityError


class TestIntegrityError:
    def test_base_exception(self) -> None:
        err = IntegrityError("integrity error")
        assert str(err) == "integrity error"
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestFileNotFoundError:
    def test_default_code(self) -> None:
        err = FileNotFoundError("file not found")
        assert err.code == ErrorCode.NOT_FOUND

    def test_inheritance(self) -> None:
        err = FileNotFoundError("not found")
        assert isinstance(err, IntegrityError)
