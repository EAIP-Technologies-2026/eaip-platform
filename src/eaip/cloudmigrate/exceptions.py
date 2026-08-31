"""Cloud migration exception hierarchy."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class MigrationError(EAIPError):
    """Base exception for all migration-related errors."""

    default_code: ErrorCode = ErrorCode.UNKNOWN

    def __init__(self, message: str) -> None:
        super().__init__(message)


class AssessmentNotFoundError(MigrationError):
    """Raised when a requested assessment is not found."""

    default_code: ErrorCode = ErrorCode.NOT_FOUND

    def __init__(self, message: str) -> None:
        super().__init__(message)


class PlanNotFoundError(MigrationError):
    """Raised when a requested migration plan is not found."""

    default_code: ErrorCode = ErrorCode.NOT_FOUND

    def __init__(self, message: str) -> None:
        super().__init__(message)
