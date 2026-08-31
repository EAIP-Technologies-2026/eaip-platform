"""Tests for :mod:`eaip.phealth.exceptions`."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode
from eaip.phealth.exceptions import HealthMetricNotFoundError, PlatformHealthError


class TestPlatformHealthExceptionHierarchy:
    """Tests for the platform health exception hierarchy."""

    def test_platform_health_error_is_eaip_error(self) -> None:
        """Test that PlatformHealthError extends EAIPError."""
        assert issubclass(PlatformHealthError, EAIPError)

    def test_metric_not_found_is_platform_health_error(self) -> None:
        """Test that HealthMetricNotFoundError extends PlatformHealthError."""
        assert issubclass(HealthMetricNotFoundError, PlatformHealthError)


class TestErrorCodes:
    """Tests for error codes on platform health exceptions."""

    def test_platform_health_error_code(self) -> None:
        """Test the default error code for PlatformHealthError."""
        err = PlatformHealthError("test")
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_metric_not_found_code(self) -> None:
        """Test the default error code for HealthMetricNotFoundError."""
        err = HealthMetricNotFoundError("not found")
        assert err.code == ErrorCode.NOT_FOUND


class TestErrorMessage:
    """Tests for error messages on platform health exceptions."""

    def test_message_preserved(self) -> None:
        """Test that the error message is preserved."""
        err = HealthMetricNotFoundError("Custom message")
        assert str(err) == "Custom message"

    def test_context_supported(self) -> None:
        """Test that context is supported on exceptions."""
        err = PlatformHealthError("error", context={"component": "api"})
        assert err.context["component"] == "api"
