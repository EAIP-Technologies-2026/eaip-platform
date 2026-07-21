"""Tests for :mod:`eaip.throttle.exceptions`."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode
from eaip.throttle.exceptions import RateLimitExceededError, ThrottleConfigError, ThrottleError


class TestThrottleExceptionHierarchy:
    """Tests for the throttle exception hierarchy."""

    def test_throttle_error_is_eaip_error(self) -> None:
        """Test that ThrottleError extends EAIPError."""
        assert issubclass(ThrottleError, EAIPError)

    def test_rate_limit_exceeded_is_throttle_error(self) -> None:
        """Test that RateLimitExceededError extends ThrottleError."""
        assert issubclass(RateLimitExceededError, ThrottleError)

    def test_config_error_is_throttle_error(self) -> None:
        """Test that ThrottleConfigError extends ThrottleError."""
        assert issubclass(ThrottleConfigError, ThrottleError)


class TestErrorCodes:
    """Tests for error codes on throttle exceptions."""

    def test_throttle_error_code(self) -> None:
        """Test the default error code for ThrottleError."""
        err = ThrottleError("test")
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_rate_limit_code(self) -> None:
        """Test the default error code for RateLimitExceededError."""
        err = RateLimitExceededError("rate limited")
        assert err.code == ErrorCode.RATE_LIMITED

    def test_config_error_code(self) -> None:
        """Test the default error code for ThrottleConfigError."""
        err = ThrottleConfigError("config error")
        assert err.code == ErrorCode.CONFIGURATION_INVALID


class TestErrorMessage:
    """Tests for error messages on throttle exceptions."""

    def test_message_preserved(self) -> None:
        """Test that the error message is preserved."""
        err = RateLimitExceededError("Custom message")
        assert str(err) == "Custom message"

    def test_context_supported(self) -> None:
        """Test that context is supported on exceptions."""
        err = ThrottleError("error", context={"rule_id": "r1"})
        assert err.context["rule_id"] == "r1"
