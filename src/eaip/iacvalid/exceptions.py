"""Exception hierarchy for Infrastructure as Code validation."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class IaCError(EAIPError):
    """Base exception for IaC validation errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class TemplateNotFoundError(IaCError):
    """Raised when an IaC template is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "IaCError",
    "TemplateNotFoundError",
]
