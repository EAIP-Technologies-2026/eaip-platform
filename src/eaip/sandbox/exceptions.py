"""Exception hierarchy for the sandbox environment manager."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class SandboxManagerError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class EnvironmentNotFoundError(SandboxManagerError):
    default_code = ErrorCode.NOT_FOUND


class SandboxNotFoundError(SandboxManagerError):
    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "EnvironmentNotFoundError",
    "SandboxManagerError",
    "SandboxNotFoundError",
]
