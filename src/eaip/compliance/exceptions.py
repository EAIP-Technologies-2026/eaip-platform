"""Exception hierarchy for the compliance subsystem."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class ComplianceError(EAIPError):
    """Base exception for compliance-related failures."""

    default_code = ErrorCode.UNKNOWN


class RegulationNotFoundError(ComplianceError):
    """Raised when a regulation is not found."""

    default_code = ErrorCode.NOT_FOUND


class ControlNotSatisfiedError(ComplianceError):
    """Raised when a required control is not satisfied."""

    default_code = ErrorCode.POLICY_VIOLATION


class EvidenceExpiredError(ComplianceError):
    """Raised when evidence has expired."""

    default_code = ErrorCode.VALIDATION_FAILED


__all__ = [
    "ComplianceError",
    "ControlNotSatisfiedError",
    "EvidenceExpiredError",
    "RegulationNotFoundError",
]
