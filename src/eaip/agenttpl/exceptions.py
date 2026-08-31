"""Exception hierarchy for agent templates."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class TemplateError(EAIPError):
    """Base exception for agent template errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class TemplateNotFoundError(TemplateError):
    """Raised when a template is not found."""

    default_code = ErrorCode.NOT_FOUND


class TemplateValidationError(TemplateError):
    """Raised when template validation fails."""

    default_code = ErrorCode.VALIDATION_FAILED


__all__ = [
    "TemplateError",
    "TemplateNotFoundError",
    "TemplateValidationError",
]
