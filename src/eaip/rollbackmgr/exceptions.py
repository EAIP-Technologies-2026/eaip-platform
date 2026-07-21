"""Exception hierarchy for deployment rollback."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class RollbackError(EAIPError):
    """Base exception for rollback errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class DeploymentNotFoundError(RollbackError):
    """Raised when a deployment is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "DeploymentNotFoundError",
    "RollbackError",
]
