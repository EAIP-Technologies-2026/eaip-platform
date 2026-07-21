"""Exception hierarchy for rate limiting."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class RateLimitError(EAIPError):
    """Base exception for rate limiting errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class RateLimitExceededError(RateLimitError):
    """Raised when a rate limit is exceeded and the request is rejected."""

    default_code = ErrorCode.RATE_LIMITED


__all__ = [
    "RateLimitError",
    "RateLimitExceededError",
]
