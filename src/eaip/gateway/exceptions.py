"""Gateway-specific exception hierarchy."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class GatewayError(EAIPError):
    """Base exception for all gateway errors."""

    default_code = ErrorCode.GATEWAY_ERROR


class EndpointNotFoundError(GatewayError):
    """Raised when a requested endpoint is not registered."""

    default_code = ErrorCode.ENDPOINT_NOT_FOUND


class AuthError(GatewayError):
    """Raised when authentication or authorisation fails."""

    default_code = ErrorCode.AUTH_FAILED


class RateLimitExceededError(GatewayError):
    """Raised when a rate limit is exceeded."""

    default_code = ErrorCode.RATE_LIMITED


__all__ = [
    "AuthError",
    "EndpointNotFoundError",
    "GatewayError",
    "RateLimitExceededError",
]
