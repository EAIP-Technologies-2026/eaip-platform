"""Change log service exception hierarchy."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class ChangeLogError(EAIPError):
    """Base exception for all change log service errors."""

    default_code: ErrorCode = ErrorCode.UNKNOWN

    def __init__(self, message: str) -> None:
        super().__init__(message)
