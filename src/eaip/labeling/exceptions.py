"""Exception hierarchy for data labeling."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class LabelingError(EAIPError):
    """Base exception for data labeling errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class TaskNotFoundError(LabelingError):
    """Raised when a labeling task is not found."""

    default_code = ErrorCode.NOT_FOUND


class LabelConflictError(LabelingError):
    """Raised when a label conflict is detected."""

    default_code = ErrorCode.REGISTRY_DUPLICATE


__all__ = [
    "LabelConflictError",
    "LabelingError",
    "TaskNotFoundError",
]
