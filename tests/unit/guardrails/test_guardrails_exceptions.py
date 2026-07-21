"""Tests for :mod:`eaip.guardrails.exceptions`."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode
from eaip.guardrails.exceptions import GuardrailConfigError, GuardrailError, GuardrailViolationError


class TestGuardrailExceptionHierarchy:
    """Tests for the guardrails exception hierarchy."""

    def test_guardrail_error_is_eaip_error(self) -> None:
        """Test that GuardrailError extends EAIPError."""
        assert issubclass(GuardrailError, EAIPError)

    def test_guardrail_violation_is_guardrail_error(self) -> None:
        """Test that GuardrailViolationError extends GuardrailError."""
        assert issubclass(GuardrailViolationError, GuardrailError)

    def test_guardrail_config_is_guardrail_error(self) -> None:
        """Test that GuardrailConfigError extends GuardrailError."""
        assert issubclass(GuardrailConfigError, GuardrailError)


class TestErrorCodes:
    """Tests for error codes on guardrails exceptions."""

    def test_guardrail_error_code(self) -> None:
        """Test the default error code for GuardrailError."""
        err = GuardrailError("test")
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_violation_error_code(self) -> None:
        """Test the default error code for GuardrailViolationError."""
        err = GuardrailViolationError("violation")
        assert err.code == ErrorCode.POLICY_VIOLATION

    def test_config_error_code(self) -> None:
        """Test the default error code for GuardrailConfigError."""
        err = GuardrailConfigError("config error")
        assert err.code == ErrorCode.CONFIGURATION_INVALID


class TestErrorMessage:
    """Tests for error messages on guardrails exceptions."""

    def test_message_preserved(self) -> None:
        """Test that the error message is preserved."""
        err = GuardrailError("Custom message")
        assert str(err) == "Custom message"

    def test_context_supported(self) -> None:
        """Test that context is supported on exceptions."""
        err = GuardrailViolationError("violation", context={"rule": "r1"})
        assert err.context["rule"] == "r1"
