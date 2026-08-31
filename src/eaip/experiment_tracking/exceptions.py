"""Experiment tracking exception hierarchy."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class ExperimentTrackingError(EAIPError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR


class ExperimentNotFoundError(ExperimentTrackingError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND

    def __init__(self, experiment_id: str) -> None:
        self.experiment_id = experiment_id
        super().__init__(f"experiment not found: {experiment_id!r}")


class ExperimentConfigError(ExperimentTrackingError):
    default_code: ErrorCode = ErrorCode.CONFIGURATION_INVALID

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ExperimentRunError(ExperimentTrackingError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ExperimentActivationError(ExperimentTrackingError):
    default_code: ErrorCode = ErrorCode.LIFECYCLE_FORBIDDEN

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ExperimentAnalysisError(ExperimentTrackingError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ExperimentAssignmentError(ExperimentTrackingError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)


__all__ = [
    "ExperimentActivationError",
    "ExperimentAnalysisError",
    "ExperimentAssignmentError",
    "ExperimentConfigError",
    "ExperimentNotFoundError",
    "ExperimentRunError",
    "ExperimentTrackingError",
]
