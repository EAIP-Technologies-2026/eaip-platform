"""Catalog of marketplace packages — registration, search, and version management."""

from __future__ import annotations

from eaip.marketplace.exceptions import PackageNotFoundError
from eaip.marketplace.models import (
    MarketplacePackage,
    PackageStatus,
    PackageType,
    PackageVersion,
)


class MarketplaceRegistry:
    """In-memory catalog of marketplace packages.

    Supports registration, lookup by various criteria, version tracking,
    and download-count bookkeeping.
    """

    def __init__(self) -> None:
        self._packages: dict[str, MarketplacePackage] = {}
        self._versions: dict[str, list[PackageVersion]] = {}

    def register(self, package: MarketplacePackage) -> None:
        self._packages[package.package_id] = package
        if package.package_id not in self._versions:
            self._versions[package.package_id] = []

    def get(self, package_id: str) -> MarketplacePackage:
        if package_id not in self._packages:
            raise PackageNotFoundError(f"Package {package_id!r} not found")
        return self._packages[package_id]

    def get_by_name(self, name: str) -> list[MarketplacePackage]:
        return [p for p in self._packages.values() if p.name == name]

    def has(self, package_id: str) -> bool:
        return package_id in self._packages

    def unregister(self, package_id: str) -> None:
        if package_id not in self._packages:
            raise PackageNotFoundError(f"Package {package_id!r} not found")
        del self._packages[package_id]
        self._versions.pop(package_id, None)

    def all(self) -> list[MarketplacePackage]:
        return list(self._packages.values())

    def search(
        self,
        *,
        query: str | None = None,
        type_filter: PackageType | None = None,
        status_filter: PackageStatus | None = None,
        tag: str | None = None,
    ) -> list[MarketplacePackage]:
        results = list(self._packages.values())

        if query:
            q = query.lower()
            results = [p for p in results if q in p.name.lower() or q in p.description.lower()]
        if type_filter:
            results = [p for p in results if p.type is type_filter]
        if status_filter:
            results = [p for p in results if p.status is status_filter]
        if tag:
            results = [p for p in results if tag in p.tags]

        return results

    def update_status(self, package_id: str, status: PackageStatus) -> MarketplacePackage:
        pkg = self.get(package_id)
        updated = pkg.model_copy(update={"status": status})
        self._packages[package_id] = updated
        return updated

    def increment_downloads(self, package_id: str) -> MarketplacePackage:
        pkg = self.get(package_id)
        updated = pkg.model_copy(update={"downloads": pkg.downloads + 1})
        self._packages[package_id] = updated
        return updated

    def add_version(self, version: PackageVersion) -> None:
        self._versions.setdefault(version.package_id, []).append(version)

    def get_versions(self, package_id: str) -> list[PackageVersion]:
        return self._versions.get(package_id, [])

    def get_latest_version(self, package_id: str) -> PackageVersion | None:
        versions = self.get_versions(package_id)
        if not versions:
            return None
        return max(versions, key=lambda v: v.created_at)

    def all_published(self) -> list[MarketplacePackage]:
        return [p for p in self._packages.values() if p.status is PackageStatus.PUBLISHED]

    def __len__(self) -> int:
        return len(self._packages)

    def __contains__(self, package_id: str) -> bool:
        return package_id in self._packages
