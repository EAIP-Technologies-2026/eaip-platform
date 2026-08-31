"""Exception hierarchy for the masking policy module."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class MaskPolicyError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class PolicyNotFoundError(MaskPolicyError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


__all__ = [
    "MaskPolicyError",
    "PolicyNotFoundError",
]
