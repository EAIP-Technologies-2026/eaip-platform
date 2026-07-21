"""Exception hierarchy for the operations package."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class OperationsError(EAIPError):
    """Base exception for all operations-package errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class MaintenanceActiveError(OperationsError):
    """Raised when an operation cannot proceed due to active maintenance."""

    default_code = ErrorCode.POLICY_VIOLATION


class BackupNotFoundError(OperationsError):
    """Raised when a requested backup does not exist."""

    default_code = ErrorCode.NOT_FOUND


class BackupRestoreError(OperationsError):
    """Raised when a backup restore operation fails."""

    default_code = ErrorCode.INTERNAL_ERROR


class MigrationError(OperationsError):
    """Raised when a migration operation fails."""

    default_code = ErrorCode.INTERNAL_ERROR


class MigrationValidationError(MigrationError):
    """Raised when a migration plan fails validation."""

    default_code = ErrorCode.VALIDATION_FAILED


class SnapshotError(OperationsError):
    """Raised when a health snapshot operation fails."""

    default_code = ErrorCode.INTERNAL_ERROR


__all__ = [
    "BackupNotFoundError",
    "BackupRestoreError",
    "MaintenanceActiveError",
    "MigrationError",
    "MigrationValidationError",
    "OperationsError",
    "SnapshotError",
]
