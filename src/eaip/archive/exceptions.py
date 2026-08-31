"""Exception hierarchy for the archival subsystem."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class ArchiveError(EAIPError):
    """Base exception for all archival errors."""

    default_code = ErrorCode.UNKNOWN
    default_severity = ErrorSeverity.ERROR


class ArchiveNotFoundError(ArchiveError):
    """Raised when an archive record is not found."""

    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING

    def __init__(self, record_id: str) -> None:
        """Initialize the exception with the missing record identifier."""
        self.record_id = record_id
        super().__init__(f"archive record not found: {record_id!r}")


class ArchiveStorageError(ArchiveError):
    """Raised when a storage backend operation fails."""

    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR

    def __init__(self, message: str) -> None:
        """Initialize the exception with a descriptive message."""
        super().__init__(message)


class RetentionPolicyViolationError(ArchiveError):
    """Raised when a retention policy constraint is violated."""

    default_code = ErrorCode.POLICY_VIOLATION
    default_severity = ErrorSeverity.WARNING

    def __init__(self, policy_id: str, message: str) -> None:
        """Initialize the exception with the policy identifier and a message."""
        self.policy_id = policy_id
        super().__init__(message)


__all__ = [
    "ArchiveError",
    "ArchiveNotFoundError",
    "ArchiveStorageError",
    "RetentionPolicyViolationError",
]
