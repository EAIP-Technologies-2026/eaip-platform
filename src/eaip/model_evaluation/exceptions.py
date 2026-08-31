"""Exception hierarchy for model evaluation and benchmarking."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class ModelEvaluationError(EAIPError):
    """Base exception for model evaluation errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class EvaluationNotFoundError(ModelEvaluationError):
    """Raised when an evaluation is not found."""

    default_code = ErrorCode.NOT_FOUND


class EvaluationFailedError(ModelEvaluationError):
    """Raised when an evaluation fails to complete."""

    default_code = ErrorCode.INTERNAL_ERROR


class EvaluationConfigError(ModelEvaluationError):
    """Raised when an evaluation configuration is invalid."""

    default_code = ErrorCode.CONFIGURATION_INVALID


class BenchmarkNotFoundError(ModelEvaluationError):
    """Raised when a benchmark is not found."""

    default_code = ErrorCode.NOT_FOUND


class BenchmarkFailedError(ModelEvaluationError):
    """Raised when a benchmark fails to complete."""

    default_code = ErrorCode.INTERNAL_ERROR


class BenchmarkConfigError(ModelEvaluationError):
    """Raised when a benchmark configuration is invalid."""

    default_code = ErrorCode.CONFIGURATION_INVALID


class ModelProfileError(ModelEvaluationError):
    """Raised when a model performance profile operation fails."""

    default_code = ErrorCode.INTERNAL_ERROR


__all__ = [
    "BenchmarkConfigError",
    "BenchmarkFailedError",
    "BenchmarkNotFoundError",
    "EvaluationConfigError",
    "EvaluationFailedError",
    "EvaluationNotFoundError",
    "ModelEvaluationError",
    "ModelProfileError",
]
