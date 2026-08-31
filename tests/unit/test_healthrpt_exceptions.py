"""Tests for :mod:`eaip.healthrpt.exceptions`."""

from __future__ import annotations

from eaip.exceptions.base import ErrorCode
from eaip.healthrpt.exceptions import ComponentNotFoundError, ReporterError


class TestReporterError:
    def test_base_exception(self) -> None:
        err = ReporterError("reporter failed")
        assert str(err) == "reporter failed"
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestComponentNotFoundError:
    def test_default_code(self) -> None:
        err = ComponentNotFoundError("component not found")
        assert err.code == ErrorCode.NOT_FOUND

    def test_inheritance(self) -> None:
        err = ComponentNotFoundError("not found")
        assert isinstance(err, ReporterError)
