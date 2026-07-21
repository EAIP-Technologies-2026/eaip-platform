"""Exception hierarchy for the secrets distribution service."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class DistributorError(EAIPError):
    """Base exception for secrets distribution errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class TargetNotFoundError(DistributorError):
    """Raised when a distribution target is not found."""

    default_code = ErrorCode.NOT_FOUND


class DistributionFailedError(DistributorError):
    """Raised when a secret distribution attempt fails."""

    default_code = ErrorCode.GATEWAY_ERROR


__all__ = [
    "DistributionFailedError",
    "DistributorError",
    "TargetNotFoundError",
]
