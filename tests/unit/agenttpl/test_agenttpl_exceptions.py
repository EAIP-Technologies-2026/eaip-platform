"""Tests for :mod:`eaip.agenttpl.exceptions`."""

from __future__ import annotations

from eaip.agenttpl.exceptions import TemplateError, TemplateNotFoundError, TemplateValidationError
from eaip.exceptions.base import EAIPError, ErrorCode


class TestTemplateExceptionHierarchy:
    """Tests for the template exception hierarchy."""

    def test_template_error_is_eaip_error(self) -> None:
        """Test that TemplateError extends EAIPError."""
        assert issubclass(TemplateError, EAIPError)

    def test_not_found_is_template_error(self) -> None:
        """Test that TemplateNotFoundError extends TemplateError."""
        assert issubclass(TemplateNotFoundError, TemplateError)

    def test_validation_is_template_error(self) -> None:
        """Test that TemplateValidationError extends TemplateError."""
        assert issubclass(TemplateValidationError, TemplateError)


class TestErrorCodes:
    """Tests for error codes on template exceptions."""

    def test_template_error_code(self) -> None:
        """Test the default error code for TemplateError."""
        err = TemplateError("test")
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_not_found_code(self) -> None:
        """Test the default error code for TemplateNotFoundError."""
        err = TemplateNotFoundError("not found")
        assert err.code == ErrorCode.NOT_FOUND

    def test_validation_code(self) -> None:
        """Test the default error code for TemplateValidationError."""
        err = TemplateValidationError("validation")
        assert err.code == ErrorCode.VALIDATION_FAILED


class TestErrorMessage:
    """Tests for error messages on template exceptions."""

    def test_message_preserved(self) -> None:
        """Test that the error message is preserved."""
        err = TemplateNotFoundError("Custom message")
        assert str(err) == "Custom message"

    def test_context_supported(self) -> None:
        """Test that context is supported on exceptions."""
        err = TemplateValidationError("bad", context={"template_id": "t1"})
        assert err.context["template_id"] == "t1"
