"""Compliance report generator exception hierarchy."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class ComplianceGenError(EAIPError):
    """Base exception for all compliance generator errors."""

    default_code: ErrorCode = ErrorCode.UNKNOWN

    def __init__(self, message: str) -> None:
        super().__init__(message)


class FrameworkNotFoundError(ComplianceGenError):
    """Raised when a requested compliance framework is not found."""

    default_code: ErrorCode = ErrorCode.NOT_FOUND

    def __init__(self, message: str) -> None:
        super().__init__(message)
