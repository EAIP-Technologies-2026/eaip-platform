"""Tests for :mod:`eaip.depscan.exceptions`."""

from __future__ import annotations

from eaip.depscan.exceptions import ScanError, TargetNotFoundError
from eaip.exceptions.base import ErrorCode


class TestScanError:
    def test_base_exception(self) -> None:
        err = ScanError("scan error")
        assert str(err) == "scan error"
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestTargetNotFoundError:
    def test_default_code(self) -> None:
        err = TargetNotFoundError("target not found")
        assert err.code == ErrorCode.NOT_FOUND

    def test_inheritance(self) -> None:
        err = TargetNotFoundError("not found")
        assert isinstance(err, ScanError)
