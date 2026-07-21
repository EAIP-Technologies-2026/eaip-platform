"""Exception hierarchy for environment variable management."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class EnvMgrError(EAIPError):
    """Base exception for environment variable management errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class VariableNotFoundError(EnvMgrError):
    """Raised when an environment variable is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "EnvMgrError",
    "VariableNotFoundError",
]
