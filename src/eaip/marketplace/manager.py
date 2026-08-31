"""Package lifecycle manager — install, uninstall, and track installations."""

from __future__ import annotations

from uuid import uuid4

from eaip.logging.context import get_logger
from eaip.marketplace.exceptions import (
    DependencyNotSatisfiedError,
    PackageAlreadyInstalledError,
    PackageNotCompatibleError,
    PackageNotFoundError,
)
from eaip.marketplace.models import (
    PackageInstallation,
    PackageStatus,
)
from eaip.marketplace.registry import MarketplaceRegistry


class PackageManager:
    """Manages package installation lifecycle."""

    def __init__(self, registry: MarketplaceRegistry | None = None) -> None:
        self._registry = registry if registry is not None else MarketplaceRegistry()
        self._installations: dict[str, PackageInstallation] = {}
        self._log = get_logger("eaip.marketplace.manager")

    @property
    def registry(self) -> MarketplaceRegistry:
        return self._registry

    async def install(
        self,
        package_id: str,
        *,
        version: str | None = None,
        installed_by: str = "system",
    ) -> PackageInstallation:
        pkg = self._registry.get(package_id)

        if pkg.status is not PackageStatus.PUBLISHED:
            raise PackageNotCompatibleError(
                f"Package {package_id!r} is not published (status: {pkg.status.value})"
            )

        if version is not None:
            versions = self._registry.get_versions(package_id)
            matched = [v for v in versions if v.version == version]
            if not matched:
                raise PackageNotFoundError(
                    f"Version {version!r} of package {package_id!r} not found"
                )
            if not matched[0].is_compatible:
                raise PackageNotCompatibleError(
                    f"Version {version!r} of package {package_id!r} is not compatible"
                )
        else:
            latest = self._registry.get_latest_version(package_id)
            if latest is None:
                raise PackageNotFoundError(f"No versions available for package {package_id!r}")
            version = latest.version

        for dep in pkg.dependencies:
            if dep not in self._registry:
                raise DependencyNotSatisfiedError(f"Dependency {dep!r} is not registered")

        existing = [
            inst
            for inst in self._installations.values()
            if inst.package_id == package_id and inst.status == "active"
        ]
        if existing:
            raise PackageAlreadyInstalledError(f"Package {package_id!r} is already installed")

        installation = PackageInstallation(
            installation_id=str(uuid4()),
            package_id=package_id,
            version=version,
            installed_by=installed_by,
            status="active",
        )
        self._installations[installation.installation_id] = installation

        self._log.info(
            "marketplace.package.installed",
            package_id=package_id,
            version=version,
            installation_id=installation.installation_id,
        )

        return installation

    async def uninstall(
        self,
        installation_id: str,
        *,
        reason: str = "",
    ) -> None:
        if installation_id not in self._installations:
            raise PackageNotFoundError(f"Installation {installation_id!r} not found")

        installation = self._installations[installation_id]
        updated = installation.model_copy(update={"status": "uninstalled"})
        self._installations[installation_id] = updated

        self._log.info(
            "marketplace.package.uninstalled",
            package_id=installation.package_id,
            installation_id=installation_id,
            reason=reason,
        )

    def get_installation(self, installation_id: str) -> PackageInstallation:
        if installation_id not in self._installations:
            raise PackageNotFoundError(f"Installation {installation_id!r} not found")
        return self._installations[installation_id]

    def list_installations(
        self,
        *,
        package_id: str | None = None,
        status: str | None = None,
    ) -> list[PackageInstallation]:
        results = list(self._installations.values())
        if package_id is not None:
            results = [i for i in results if i.package_id == package_id]
        if status is not None:
            results = [i for i in results if i.status == status]
        return results


__all__ = ["PackageManager"]
