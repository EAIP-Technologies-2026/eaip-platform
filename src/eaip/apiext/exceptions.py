"""API Extensions exception hierarchy."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class ApiExtError(EAIPError):
    """Base exception for all API Extensions errors."""

    default_code = ErrorCode.APIEXT_ERROR


class CompositionError(ApiExtError):
    """Raised when API composition fails."""

    default_code = ErrorCode.COMPOSITION_ERROR


class CacheError(ApiExtError):
    """Raised when the response cache encounters an error."""

    default_code = ErrorCode.CACHE_ERROR


class RateLimitExceededError(ApiExtError):
    """Raised when a rate-limit policy is exceeded."""

    default_code = ErrorCode.RATE_LIMIT_POLICY_ERROR


class TransformError(ApiExtError):
    """Raised when a response transformation fails."""

    default_code = ErrorCode.TRANSFORM_ERROR


class PolicyNotFoundError(ApiExtError):
    """Raised when a requested policy is not found."""

    default_code = ErrorCode.POLICY_NOT_FOUND


__all__ = [
    "ApiExtError",
    "CacheError",
    "CompositionError",
    "PolicyNotFoundError",
    "RateLimitExceededError",
    "TransformError",
]
