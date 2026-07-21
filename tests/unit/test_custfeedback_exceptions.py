"""Tests for :mod:`eaip.custfeedback.exceptions`."""

from __future__ import annotations

from eaip.custfeedback.exceptions import FeedbackError, FeedbackNotFoundError
from eaip.exceptions import ErrorCode


class TestFeedbackError:
    def test_default_code(self) -> None:
        err = FeedbackError("Analysis failed")
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestFeedbackNotFoundError:
    def test_default_code(self) -> None:
        err = FeedbackNotFoundError("Feedback not found")
        assert err.code == ErrorCode.NOT_FOUND

    def test_inheritance(self) -> None:
        assert issubclass(FeedbackNotFoundError, FeedbackError)
