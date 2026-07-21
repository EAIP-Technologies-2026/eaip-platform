"""Package publisher — publish, update, and deprecate marketplace packages."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from eaip.logging.context import get_logger
from eaip.marketplace.exceptions import (
    PackageNotCompatibleError,
)
from eaip.marketplace.models import (
    MarketplacePackage,
    PackageStatus,
)
from eaip.marketplace.registry import MarketplaceRegistry


class Publisher:
    """Service for publishing and managing packages in the marketplace."""

    def __init__(self, registry: MarketplaceRegistry | None = None) -> None:
        self._registry = registry or MarketplaceRegistry()
        self._log = get_logger("eaip.marketplace.publisher")

    @property
    def registry(self) -> MarketplaceRegistry:
        return self._registry

    async def publish(self, package: MarketplacePackage) -> MarketplacePackage:
        package_id = package.package_id or str(uuid4())
        pkg = package.model_copy(update={"package_id": package_id})
        self._registry.register(pkg)

        self._log.info(
            "marketplace.package.published",
            package_id=package_id,
            name=pkg.name,
            version=pkg.version,
        )

        return pkg

    async def update(
        self,
        package_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        version: str | None = None,
        tags: tuple[str, ...] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> MarketplacePackage:
        existing = self._registry.get(package_id)

        updates: dict[str, Any] = {}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        if version is not None:
            updates["version"] = version
        if tags is not None:
            updates["tags"] = tags
        if metadata is not None:
            merged = dict(existing.metadata)
            merged.update(metadata)
            updates["metadata"] = merged

        if not updates:
            return existing

        updates["updated_at"] = datetime.now()

        updated = existing.model_copy(update=updates)
        self._registry._packages[package_id] = updated

        self._log.info(
            "marketplace.package.updated",
            package_id=package_id,
            updates=list(updates.keys()),
        )

        return updated

    async def deprecate(
        self,
        package_id: str,
        *,
        reason: str = "",
    ) -> MarketplacePackage:
        pkg = self._registry.get(package_id)

        if pkg.status is PackageStatus.DEPRECATED:
            raise PackageNotCompatibleError(f"Package {package_id!r} is already deprecated")

        updated = self._registry.update_status(package_id, PackageStatus.DEPRECATED)

        self._log.info(
            "marketplace.package.deprecated",
            package_id=package_id,
            reason=reason,
        )

        return updated


__all__ = ["Publisher"]
