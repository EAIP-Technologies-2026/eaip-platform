"""Exception hierarchy for the feature flag & experimentation engine."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class FeatureError(EAIPError):
    """Base exception for feature-flag-related errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class FlagNotFoundError(FeatureError):
    """Raised when a requested feature flag does not exist."""

    default_code = ErrorCode.NOT_FOUND


class ExperimentNotFoundError(FeatureError):
    """Raised when a requested experiment does not exist."""

    default_code = ErrorCode.NOT_FOUND


class FlagNotEnabledError(FeatureError):
    """Raised when a disabled flag is evaluated or a rollout action is attempted."""

    default_code = ErrorCode.LIFECYCLE_FORBIDDEN


class ExperimentCompleteError(FeatureError):
    """Raised when an action is attempted on a completed experiment."""

    default_code = ErrorCode.LIFECYCLE_FORBIDDEN


class InvalidRolloutError(FeatureError):
    """Raised when rollout parameters are invalid."""

    default_code = ErrorCode.VALIDATION_FAILED


__all__ = [
    "ExperimentCompleteError",
    "ExperimentNotFoundError",
    "FeatureError",
    "FlagNotEnabledError",
    "FlagNotFoundError",
    "InvalidRolloutError",
]
