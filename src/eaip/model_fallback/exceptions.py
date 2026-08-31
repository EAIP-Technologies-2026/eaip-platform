"""Exception hierarchy for the model fallback subsystem."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class ModelFallbackError(EAIPError):
    """Base exception for model fallback failures."""

    default_code = ErrorCode.INTERNAL_ERROR


class FallbackConfigError(ModelFallbackError):
    """Raised when there is a fallback configuration error."""

    default_code = ErrorCode.CONFIGURATION_INVALID


class FallbackChainError(ModelFallbackError):
    """Raised when a fallback chain operation fails."""

    default_code = ErrorCode.INTERNAL_ERROR


class FallbackExecutionError(ModelFallbackError):
    """Raised when a fallback chain execution fails."""

    default_code = ErrorCode.INTERNAL_ERROR


class FallbackStepError(ModelFallbackError):
    """Raised when an individual fallback step fails."""

    default_code = ErrorCode.INTERNAL_ERROR


class FallbackTriggerError(ModelFallbackError):
    """Raised when a fallback trigger condition is misconfigured."""

    default_code = ErrorCode.CONFIGURATION_INVALID


class DegradationError(ModelFallbackError):
    """Raised when graceful degradation encounters an error."""

    default_code = ErrorCode.INTERNAL_ERROR


__all__ = [
    "DegradationError",
    "FallbackChainError",
    "FallbackConfigError",
    "FallbackExecutionError",
    "FallbackStepError",
    "FallbackTriggerError",
    "ModelFallbackError",
]
