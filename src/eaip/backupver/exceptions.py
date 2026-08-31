"""Exception hierarchy for backup verification."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class BackupVerificationError(EAIPError):
    """Base exception for backup verification errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class BackupNotFoundError(BackupVerificationError):
    """Raised when a backup record is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "BackupNotFoundError",
    "BackupVerificationError",
]
