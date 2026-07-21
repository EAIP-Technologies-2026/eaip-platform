"""Tests for :mod:`eaip.reportsched.exceptions`."""

from __future__ import annotations

from eaip.exceptions.base import ErrorCode
from eaip.reportsched.exceptions import ReportGenerationError, ReportNotFoundError, SchedulerError


class TestSchedulerError:
    def test_base_exception(self) -> None:
        err = SchedulerError("scheduler error")
        assert str(err) == "scheduler error"
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestReportNotFoundError:
    def test_default_code(self) -> None:
        err = ReportNotFoundError("report not found")
        assert err.code == ErrorCode.NOT_FOUND

    def test_inheritance(self) -> None:
        err = ReportNotFoundError("not found")
        assert isinstance(err, SchedulerError)


class TestReportGenerationError:
    def test_default_code(self) -> None:
        err = ReportGenerationError("generation failed")
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_inheritance(self) -> None:
        err = ReportGenerationError("failed")
        assert isinstance(err, SchedulerError)
