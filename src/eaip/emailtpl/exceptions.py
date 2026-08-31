"""Exception hierarchy for email template design."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class TemplateDesignError(EAIPError):
    """Base exception for email template design errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class TemplateNotFoundError(TemplateDesignError):
    """Raised when an email template is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "TemplateDesignError",
    "TemplateNotFoundError",
]
