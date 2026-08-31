"""Configuration backup service exception hierarchy."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class ConfigBackupError(EAIPError):
    """Base exception for all config backup errors."""

    default_code: ErrorCode = ErrorCode.UNKNOWN

    def __init__(self, message: str) -> None:
        super().__init__(message)


class SnapshotNotFoundError(ConfigBackupError):
    """Raised when a requested snapshot is not found."""

    default_code: ErrorCode = ErrorCode.NOT_FOUND

    def __init__(self, message: str) -> None:
        super().__init__(message)
