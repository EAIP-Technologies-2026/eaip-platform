"""Exception hierarchy for the Developer API & SDK Platform."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class DevPlatformError(EAIPError):
    """Base exception for all dev-platform errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class VersionNotFoundError(DevPlatformError):
    """Raised when a requested API version does not exist."""

    default_code = ErrorCode.NOT_FOUND


class KeyNotFoundError(DevPlatformError):
    """Raised when a requested developer key does not exist."""

    default_code = ErrorCode.NOT_FOUND


class KeyExpiredError(DevPlatformError):
    """Raised when a developer key has expired."""

    default_code = ErrorCode.AUTH_FAILED


class RateLimitExceededError(DevPlatformError):
    """Raised when a developer key exceeds its rate limit."""

    default_code = ErrorCode.RATE_LIMITED


class PlaygroundError(DevPlatformError):
    """Raised when a playground operation fails."""

    default_code = ErrorCode.INTERNAL_ERROR


__all__ = [
    "DevPlatformError",
    "KeyExpiredError",
    "KeyNotFoundError",
    "PlaygroundError",
    "RateLimitExceededError",
    "VersionNotFoundError",
]
