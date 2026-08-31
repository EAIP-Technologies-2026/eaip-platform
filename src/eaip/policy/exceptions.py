"""Policy-specific exceptions."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class PolicyError(EAIPError):
    """Base for policy-related failures."""

    default_code = ErrorCode.POLICY_VIOLATION


class PolicyViolationError(EAIPError):
    """Raised when a request is denied by the authorization manager."""

    default_code = ErrorCode.POLICY_VIOLATION


__all__ = ["PolicyError", "PolicyViolationError"]
