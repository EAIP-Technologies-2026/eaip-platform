"""Marketplace-specific exception hierarchy."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class MarketplaceError(EAIPError):
    """Base marketplace error."""

    default_code = ErrorCode.UNKNOWN


class PackageNotFoundError(MarketplaceError):
    """Raised when a package is not found."""

    default_code = ErrorCode.NOT_FOUND


class PackageNotCompatibleError(MarketplaceError):
    """Raised when a package is not compatible."""

    default_code = ErrorCode.VALIDATION_FAILED


class DependencyNotSatisfiedError(MarketplaceError):
    """Raised when a dependency is not satisfied."""

    default_code = ErrorCode.DEPENDENCY_MISSING


class PackageAlreadyInstalledError(MarketplaceError):
    """Raised when a package is already installed."""

    default_code = ErrorCode.REGISTRY_DUPLICATE
