"""File store exception classes."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class FileStoreError(EAIPError):
    """Base exception for file store errors."""

    default_code = ErrorCode.UNKNOWN


class FileNotFoundError(FileStoreError):
    """Raised when a file asset is not found."""

    default_code = ErrorCode.NOT_FOUND


class FileTooLargeError(FileStoreError):
    """Raised when a file exceeds the maximum upload size."""

    default_code = ErrorCode.VALIDATION_FAILED


class UnsupportedFileTypeError(FileStoreError):
    """Raised when a file type is not allowed."""

    default_code = ErrorCode.VALIDATION_FAILED


class StorageProviderError(FileStoreError):
    """Raised when a storage provider operation fails."""

    default_code = ErrorCode.PROVIDER_UNAVAILABLE


class DuplicateFileError(FileStoreError):
    """Raised when a duplicate file is detected."""

    default_code = ErrorCode.REGISTRY_DUPLICATE


__all__ = [
    "DuplicateFileError",
    "FileNotFoundError",
    "FileStoreError",
    "FileTooLargeError",
    "StorageProviderError",
    "UnsupportedFileTypeError",
]
