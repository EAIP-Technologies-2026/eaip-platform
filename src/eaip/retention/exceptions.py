"""Exception hierarchy for the data retention and purge service."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class RetentionError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class PolicyNotFoundError(RetentionError):
    default_code = ErrorCode.NOT_FOUND


class PurgeExecutionError(RetentionError):
    default_code = ErrorCode.INTERNAL_ERROR


__all__ = [
    "PolicyNotFoundError",
    "PurgeExecutionError",
    "RetentionError",
]
