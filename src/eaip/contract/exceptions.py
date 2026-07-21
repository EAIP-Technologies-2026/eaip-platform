"""Exception hierarchy for the contract management service."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class ContractError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class ContractNotFoundError(ContractError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


__all__ = [
    "ContractError",
    "ContractNotFoundError",
]
