"""Exception hierarchy for file integrity monitoring."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class IntegrityError(EAIPError):
    """Base exception for file integrity errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class FileNotFoundError(IntegrityError):
    """Raised when a monitored file is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "FileNotFoundError",
    "IntegrityError",
]
