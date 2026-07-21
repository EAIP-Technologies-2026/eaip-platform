"""Exception hierarchy for export compliance checking."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class ComplianceCheckError(EAIPError):
    """Base exception for export compliance errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class PartyNotFoundError(ComplianceCheckError):
    """Raised when a restricted party is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "ComplianceCheckError",
    "PartyNotFoundError",
]
