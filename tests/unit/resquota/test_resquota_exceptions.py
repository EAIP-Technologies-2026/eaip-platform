"""Tests for :mod:`eaip.resquota.exceptions`."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode
from eaip.resquota.exceptions import QuotaError, QuotaExceededError, QuotaNotFoundError


class TestQuotaExceptionHierarchy:
    """Tests for the quota exception hierarchy."""

    def test_quota_error_is_eaip_error(self) -> None:
        """Test that QuotaError extends EAIPError."""
        assert issubclass(QuotaError, EAIPError)

    def test_exceeded_is_quota_error(self) -> None:
        """Test that QuotaExceededError extends QuotaError."""
        assert issubclass(QuotaExceededError, QuotaError)

    def test_not_found_is_quota_error(self) -> None:
        """Test that QuotaNotFoundError extends QuotaError."""
        assert issubclass(QuotaNotFoundError, QuotaError)


class TestErrorCodes:
    """Tests for error codes on quota exceptions."""

    def test_quota_error_code(self) -> None:
        """Test the default error code for QuotaError."""
        err = QuotaError("test")
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_exceeded_code(self) -> None:
        """Test the default error code for QuotaExceededError."""
        err = QuotaExceededError("exceeded")
        assert err.code == ErrorCode.RATE_LIMITED

    def test_not_found_code(self) -> None:
        """Test the default error code for QuotaNotFoundError."""
        err = QuotaNotFoundError("not found")
        assert err.code == ErrorCode.NOT_FOUND


class TestErrorMessage:
    """Tests for error messages on quota exceptions."""

    def test_message_preserved(self) -> None:
        """Test that the error message is preserved."""
        err = QuotaNotFoundError("Custom message")
        assert str(err) == "Custom message"

    def test_context_supported(self) -> None:
        """Test that context is supported on exceptions."""
        err = QuotaExceededError("exceeded", context={"quota_id": "q1"})
        assert err.context["quota_id"] == "q1"
