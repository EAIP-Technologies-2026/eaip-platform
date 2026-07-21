"""Tests for :mod:`eaip.feedback.exceptions`."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode
from eaip.feedback.exceptions import FeedbackDuplicateError, FeedbackError, FeedbackNotFoundError


class TestFeedbackExceptionHierarchy:
    """Tests for the feedback exception hierarchy."""

    def test_feedback_error_is_eaip_error(self) -> None:
        """Test that FeedbackError extends EAIPError."""
        assert issubclass(FeedbackError, EAIPError)

    def test_not_found_is_feedback_error(self) -> None:
        """Test that FeedbackNotFoundError extends FeedbackError."""
        assert issubclass(FeedbackNotFoundError, FeedbackError)

    def test_duplicate_is_feedback_error(self) -> None:
        """Test that FeedbackDuplicateError extends FeedbackError."""
        assert issubclass(FeedbackDuplicateError, FeedbackError)


class TestErrorCodes:
    """Tests for error codes on feedback exceptions."""

    def test_feedback_error_code(self) -> None:
        """Test the default error code for FeedbackError."""
        err = FeedbackError("test")
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_not_found_code(self) -> None:
        """Test the default error code for FeedbackNotFoundError."""
        err = FeedbackNotFoundError("not found")
        assert err.code == ErrorCode.NOT_FOUND

    def test_duplicate_code(self) -> None:
        """Test the default error code for FeedbackDuplicateError."""
        err = FeedbackDuplicateError("duplicate")
        assert err.code == ErrorCode.REGISTRY_DUPLICATE


class TestErrorMessage:
    """Tests for error messages on feedback exceptions."""

    def test_message_preserved(self) -> None:
        """Test that the error message is preserved."""
        err = FeedbackNotFoundError("Custom message")
        assert str(err) == "Custom message"

    def test_context_supported(self) -> None:
        """Test that context is supported on exceptions."""
        err = FeedbackError("error", context={"feedback_id": "f1"})
        assert err.context["feedback_id"] == "f1"
