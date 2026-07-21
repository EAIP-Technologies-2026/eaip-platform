"""Exception hierarchy for model monitoring."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class ModelMonitorError(EAIPError):
    """Base exception for model monitoring errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class ModelNotFoundError(ModelMonitorError):
    """Raised when a monitored model is not found."""

    default_code = ErrorCode.MODEL_NOT_FOUND


__all__ = [
    "ModelMonitorError",
    "ModelNotFoundError",
]
