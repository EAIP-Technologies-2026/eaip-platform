"""Package discovery service — search and browse the marketplace catalog."""

from __future__ import annotations

from eaip.marketplace.exceptions import PackageNotFoundError
from eaip.marketplace.models import MarketplacePackage, PackageStatus, PackageType
from eaip.marketplace.registry import MarketplaceRegistry


class DiscoveryService:
    """Service for discovering and browsing marketplace packages."""

    def __init__(self, registry: MarketplaceRegistry | None = None) -> None:
        """Initialize the discovery service."""
        self._registry = registry or MarketplaceRegistry()

    @property
    def registry(self) -> MarketplaceRegistry:
        """Return the registry."""
        return self._registry

    def discover_packages(
        self,
        *,
        type_filter: PackageType | None = None,
        tag: str | None = None,
    ) -> list[MarketplacePackage]:
        """Discover published packages, optionally filtered."""
        return self._registry.search(
            status_filter=PackageStatus.PUBLISHED,
            type_filter=type_filter,
            tag=tag,
        )

    def get_package(self, package_id: str) -> MarketplacePackage:
        """Get a package by ID (published or deprecated only)."""
        pkg = self._registry.get(package_id)
        if pkg.status is not PackageStatus.PUBLISHED and pkg.status is not PackageStatus.DEPRECATED:
            raise PackageNotFoundError(f"Package {package_id!r} is not available")
        return pkg

    def search(
        self,
        query: str,
        *,
        type_filter: PackageType | None = None,
        tag: str | None = None,
    ) -> list[MarketplacePackage]:
        """Search published packages by query string."""
        return self._registry.search(
            query=query,
            type_filter=type_filter,
            status_filter=PackageStatus.PUBLISHED,
            tag=tag,
        )


__all__ = ["DiscoveryService"]
