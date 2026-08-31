"""Exception hierarchy for rate limiting."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class ThrottleError(EAIPError):
    """Base exception for throttling errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class RateLimitExceededError(ThrottleError):
    """Raised when a rate limit is exceeded."""

    default_code = ErrorCode.RATE_LIMITED


class ThrottleConfigError(ThrottleError):
    """Raised when throttle configuration is invalid."""

    default_code = ErrorCode.CONFIGURATION_INVALID


__all__ = [
    "RateLimitExceededError",
    "ThrottleConfigError",
    "ThrottleError",
]
