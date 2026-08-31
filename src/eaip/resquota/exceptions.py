"""Exception hierarchy for resource quotas."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class QuotaError(EAIPError):
    """Base exception for resource quota errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class QuotaExceededError(QuotaError):
    """Raised when a quota limit is exceeded."""

    default_code = ErrorCode.RATE_LIMITED


class QuotaNotFoundError(QuotaError):
    """Raised when a quota is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "QuotaError",
    "QuotaExceededError",
    "QuotaNotFoundError",
]
