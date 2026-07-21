"""Exception hierarchy for event retention management."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class EventRetentionError(EAIPError):
    """Base exception for event retention errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class PolicyNotFoundError(EventRetentionError):
    """Raised when a retention policy is not found."""

    default_code = ErrorCode.POLICY_NOT_FOUND


__all__ = [
    "EventRetentionError",
    "PolicyNotFoundError",
]
