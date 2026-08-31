"""Exception hierarchy for platform health."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class PlatformHealthError(EAIPError):
    """Base exception for platform health errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class HealthMetricNotFoundError(PlatformHealthError):
    """Raised when a health metric is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "HealthMetricNotFoundError",
    "PlatformHealthError",
]
