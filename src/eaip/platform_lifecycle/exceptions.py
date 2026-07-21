"""Exception hierarchy for platform lifecycle management."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class PlatformLifecycleError(EAIPError):
    """Base exception for platform lifecycle errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class PlatformLifecycleStateError(PlatformLifecycleError):
    """Raised when an invalid lifecycle state is encountered."""

    default_code = ErrorCode.LIFECYCLE_FORBIDDEN


class PlatformLifecycleTransitionError(PlatformLifecycleError):
    """Raised when an invalid state transition is attempted."""

    default_code = ErrorCode.LIFECYCLE_FORBIDDEN


class PlatformUpgradeError(PlatformLifecycleError):
    """Raised when a platform upgrade operation fails."""

    default_code = ErrorCode.GATEWAY_ERROR


class PlatformMigrationError(PlatformLifecycleError):
    """Raised when a platform migration operation fails."""

    default_code = ErrorCode.GATEWAY_ERROR


class PlatformComponentError(PlatformLifecycleError):
    """Raised when a component operation fails."""

    default_code = ErrorCode.PROVIDER_UNAVAILABLE


class PlatformMaintenanceError(PlatformLifecycleError):
    """Raised when a maintenance window operation fails."""

    default_code = ErrorCode.GATEWAY_ERROR


class PlatformLifecycleConfigError(PlatformLifecycleError):
    """Raised when lifecycle configuration is invalid."""

    default_code = ErrorCode.CONFIGURATION_INVALID


__all__ = [
    "PlatformComponentError",
    "PlatformLifecycleConfigError",
    "PlatformLifecycleError",
    "PlatformLifecycleStateError",
    "PlatformLifecycleTransitionError",
    "PlatformMaintenanceError",
    "PlatformMigrationError",
    "PlatformUpgradeError",
]
