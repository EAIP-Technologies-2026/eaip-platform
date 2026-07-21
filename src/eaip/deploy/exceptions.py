"""Exception hierarchy for deployment & release management."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class DeployError(EAIPError):
    """Base exception for all deployment & release management errors."""

    default_code = ErrorCode.UNKNOWN


class ReleaseNotFoundError(DeployError):
    """Raised when a requested release does not exist."""

    default_code = ErrorCode.NOT_FOUND

    def __init__(self, release_id: str) -> None:
        """Initialize the exception with the missing release identifier."""
        self.release_id = release_id
        super().__init__(f"release not found: {release_id!r}")


class DeploymentFailedError(DeployError):
    """Raised when a deployment operation fails."""

    default_code = ErrorCode.INTERNAL_ERROR

    def __init__(self, deployment_id: str, message: str) -> None:
        """Initialize the exception with deployment details and failure reason."""
        self.deployment_id = deployment_id
        super().__init__(f"deployment {deployment_id!r} failed: {message}")


class RollbackFailedError(DeployError):
    """Raised when a rollback operation fails."""

    default_code = ErrorCode.INTERNAL_ERROR

    def __init__(self, deployment_id: str, message: str) -> None:
        """Initialize the exception with deployment details and rollback failure reason."""
        self.deployment_id = deployment_id
        super().__init__(f"rollback for deployment {deployment_id!r} failed: {message}")


class InvalidEnvironmentError(DeployError):
    """Raised when an invalid environment name is provided."""

    default_code = ErrorCode.VALIDATION_FAILED

    def __init__(self, environment: str) -> None:
        """Initialize the exception with the invalid environment name."""
        self.environment = environment
        super().__init__(f"invalid environment: {environment!r}")


__all__ = [
    "DeployError",
    "DeploymentFailedError",
    "InvalidEnvironmentError",
    "ReleaseNotFoundError",
    "RollbackFailedError",
]
