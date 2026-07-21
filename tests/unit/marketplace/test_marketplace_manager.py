from __future__ import annotations

import pytest

from eaip.marketplace.exceptions import (
    DependencyNotSatisfiedError,
    PackageAlreadyInstalledError,
    PackageNotCompatibleError,
    PackageNotFoundError,
)
from eaip.marketplace.manager import PackageManager
from eaip.marketplace.models import (
    MarketplacePackage,
    PackageStatus,
    PackageType,
    PackageVersion,
)


def _make_pkg(
    package_id: str = "pkg-1",
    name: str = "test-agent",
    status: PackageStatus = PackageStatus.PUBLISHED,
    dependencies: tuple[str, ...] = (),
) -> MarketplacePackage:
    return MarketplacePackage(
        package_id=package_id,
        name=name,
        type=PackageType.AGENT,
        version="1.0.0",
        description=f"Description of {name}",
        author="developer",
        status=status,
        dependencies=dependencies,
    )


def _make_version(
    package_id: str = "pkg-1",
    version: str = "1.0.0",
    is_compatible: bool = True,
) -> PackageVersion:
    return PackageVersion(
        package_id=package_id,
        version=version,
        semver_range=f">={version}",
        changelog=f"Version {version}",
        checksum="abc123",
        size_bytes=1024,
        is_compatible=is_compatible,
    )


class TestPackageManager:
    def test_default_initialization(self) -> None:
        mgr = PackageManager()
        assert mgr.registry is not None

    def test_custom_registry(self) -> None:
        from eaip.marketplace.registry import MarketplaceRegistry

        reg = MarketplaceRegistry()
        pkg = _make_pkg()
        reg.register(pkg)
        mgr = PackageManager(registry=reg)
        assert mgr.registry is reg

    @pytest.mark.asyncio
    async def test_install_success(self) -> None:
        mgr = PackageManager()
        pkg = _make_pkg()
        ver = _make_version()
        mgr.registry.register(pkg)
        mgr.registry.add_version(ver)

        inst = await mgr.install("pkg-1")
        assert inst.package_id == "pkg-1"
        assert inst.version == "1.0.0"
        assert inst.installed_by == "system"
        assert inst.status == "active"

    @pytest.mark.asyncio
    async def test_install_with_specific_version(self) -> None:
        mgr = PackageManager()
        pkg = _make_pkg()
        v1 = _make_version(version="1.0.0")
        v2 = _make_version(version="2.0.0")
        mgr.registry.register(pkg)
        mgr.registry.add_version(v1)
        mgr.registry.add_version(v2)

        inst = await mgr.install("pkg-1", version="1.0.0")
        assert inst.version == "1.0.0"

    @pytest.mark.asyncio
    async def test_install_with_installed_by(self) -> None:
        mgr = PackageManager()
        pkg = _make_pkg()
        ver = _make_version()
        mgr.registry.register(pkg)
        mgr.registry.add_version(ver)

        inst = await mgr.install("pkg-1", installed_by="user-1")
        assert inst.installed_by == "user-1"

    @pytest.mark.asyncio
    async def test_install_package_not_found(self) -> None:
        mgr = PackageManager()
        with pytest.raises(PackageNotFoundError, match="not found"):
            await mgr.install("nonexistent")

    @pytest.mark.asyncio
    async def test_install_not_published(self) -> None:
        mgr = PackageManager()
        pkg = _make_pkg(status=PackageStatus.DRAFT)
        mgr.registry.register(pkg)
        with pytest.raises(PackageNotCompatibleError, match="not published"):
            await mgr.install("pkg-1")

    @pytest.mark.asyncio
    async def test_install_version_not_found(self) -> None:
        mgr = PackageManager()
        pkg = _make_pkg()
        mgr.registry.register(pkg)
        with pytest.raises(PackageNotFoundError, match="not found"):
            await mgr.install("pkg-1", version="9.9.9")

    @pytest.mark.asyncio
    async def test_install_version_not_compatible(self) -> None:
        mgr = PackageManager()
        pkg = _make_pkg()
        ver = _make_version(is_compatible=False)
        mgr.registry.register(pkg)
        mgr.registry.add_version(ver)
        with pytest.raises(PackageNotCompatibleError, match="not compatible"):
            await mgr.install("pkg-1", version="1.0.0")

    @pytest.mark.asyncio
    async def test_install_no_versions_available(self) -> None:
        mgr = PackageManager()
        pkg = _make_pkg()
        mgr.registry.register(pkg)
        with pytest.raises(PackageNotFoundError, match="No versions"):
            await mgr.install("pkg-1")

    @pytest.mark.asyncio
    async def test_install_dependency_not_satisfied(self) -> None:
        mgr = PackageManager()
        pkg = _make_pkg(dependencies=("dep-1",))
        ver = _make_version()
        mgr.registry.register(pkg)
        mgr.registry.add_version(ver)
        with pytest.raises(DependencyNotSatisfiedError, match="not registered"):
            await mgr.install("pkg-1")

    @pytest.mark.asyncio
    async def test_install_already_installed(self) -> None:
        mgr = PackageManager()
        pkg = _make_pkg()
        ver = _make_version()
        mgr.registry.register(pkg)
        mgr.registry.add_version(ver)

        await mgr.install("pkg-1")
        with pytest.raises(PackageAlreadyInstalledError, match="already installed"):
            await mgr.install("pkg-1")

    @pytest.mark.asyncio
    async def test_uninstall_success(self) -> None:
        mgr = PackageManager()
        pkg = _make_pkg()
        ver = _make_version()
        mgr.registry.register(pkg)
        mgr.registry.add_version(ver)

        inst = await mgr.install("pkg-1")
        await mgr.uninstall(inst.installation_id)
        retrieved = mgr.get_installation(inst.installation_id)
        assert retrieved.status == "uninstalled"

    @pytest.mark.asyncio
    async def test_uninstall_not_found(self) -> None:
        mgr = PackageManager()
        with pytest.raises(PackageNotFoundError, match="not found"):
            await mgr.uninstall("nonexistent")

    @pytest.mark.asyncio
    async def test_get_installation_success(self) -> None:
        mgr = PackageManager()
        pkg = _make_pkg()
        ver = _make_version()
        mgr.registry.register(pkg)
        mgr.registry.add_version(ver)

        inst = await mgr.install("pkg-1")
        retrieved = mgr.get_installation(inst.installation_id)
        assert retrieved.installation_id == inst.installation_id

    def test_get_installation_not_found(self) -> None:
        mgr = PackageManager()
        with pytest.raises(PackageNotFoundError, match="not found"):
            mgr.get_installation("nonexistent")

    def test_list_installations_all(self) -> None:
        mgr = PackageManager()
        assert mgr.list_installations() == []

    @pytest.mark.asyncio
    async def test_list_installations_by_package_id(self) -> None:
        mgr = PackageManager()
        pkg1 = _make_pkg(package_id="pkg-1")
        pkg2 = _make_pkg(package_id="pkg-2", name="other")
        ver1 = _make_version(package_id="pkg-1")
        ver2 = _make_version(package_id="pkg-2")
        mgr.registry.register(pkg1)
        mgr.registry.register(pkg2)
        mgr.registry.add_version(ver1)
        mgr.registry.add_version(ver2)

        inst1 = await mgr.install("pkg-1")
        await mgr.install("pkg-2")

        results = mgr.list_installations(package_id="pkg-1")
        assert len(results) == 1
        assert results[0].installation_id == inst1.installation_id

    @pytest.mark.asyncio
    async def test_list_installations_by_status(self) -> None:
        mgr = PackageManager()
        pkg = _make_pkg()
        ver = _make_version()
        mgr.registry.register(pkg)
        mgr.registry.add_version(ver)

        await mgr.install("pkg-1")

        results = mgr.list_installations(status="active")
        assert len(results) == 1

        results = mgr.list_installations(status="uninstalled")
        assert results == []
