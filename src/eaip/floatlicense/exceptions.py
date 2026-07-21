"""Exception hierarchy for floating license management."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class LicenseMgrError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class PoolNotFoundError(LicenseMgrError):
    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "LicenseMgrError",
    "PoolNotFoundError",
]
