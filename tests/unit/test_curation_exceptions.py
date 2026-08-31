"""Tests for :mod:`eaip.curation.exceptions`."""

from __future__ import annotations

from eaip.curation.exceptions import CurationError, SubmissionNotFoundError
from eaip.exceptions.base import ErrorCode


class TestCurationError:
    def test_base_exception(self) -> None:
        err = CurationError("curation failed")
        assert str(err) == "curation failed"
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestSubmissionNotFoundError:
    def test_default_code(self) -> None:
        err = SubmissionNotFoundError("submission not found")
        assert err.code == ErrorCode.NOT_FOUND

    def test_inheritance(self) -> None:
        err = SubmissionNotFoundError("not found")
        assert isinstance(err, CurationError)
