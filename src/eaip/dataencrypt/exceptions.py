"""Exception hierarchy for the data encryption module."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class EncryptionError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class KeyNotFoundError(EncryptionError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


__all__ = [
    "EncryptionError",
    "KeyNotFoundError",
]
