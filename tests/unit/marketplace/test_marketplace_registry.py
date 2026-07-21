from __future__ import annotations

import pytest

from eaip.marketplace.exceptions import PackageNotFoundError
from eaip.marketplace.models import (
    MarketplacePackage,
    PackageStatus,
    PackageType,
    PackageVersion,
)
from eaip.marketplace.registry import MarketplaceRegistry


def _make_pkg(
    package_id: str = "pkg-1",
    name: str = "test-agent",
    type_: PackageType = PackageType.AGENT,
    version: str = "1.0.0",
    status: PackageStatus = PackageStatus.DRAFT,
    tags: tuple[str, ...] = (),
) -> MarketplacePackage:
    return MarketplacePackage(
        package_id=package_id,
        name=name,
        type=type_,
        version=version,
        description=f"Description of {name}",
        author="developer",
        status=status,
        tags=tags,
    )


def _make_version(
    package_id: str = "pkg-1",
    version: str = "1.0.0",
) -> PackageVersion:
    return PackageVersion(
        package_id=package_id,
        version=version,
        semver_range=f">={version}",
        changelog=f"Version {version}",
        checksum="abc123",
        size_bytes=1024,
    )


class TestMarketplaceRegistry:
    def test_register_and_get(self) -> None:
        reg = MarketplaceRegistry()
        pkg = _make_pkg()
        reg.register(pkg)
        assert reg.get("pkg-1") is pkg

    def test_get_not_found(self) -> None:
        reg = MarketplaceRegistry()
        with pytest.raises(PackageNotFoundError, match="not found"):
            reg.get("nonexistent")

    def test_get_by_name(self) -> None:
        reg = MarketplaceRegistry()
        pkg = _make_pkg(package_id="pkg-1", name="test-agent")
        reg.register(pkg)
        results = reg.get_by_name("test-agent")
        assert len(results) == 1
        assert results[0] is pkg

    def test_get_by_name_missing(self) -> None:
        reg = MarketplaceRegistry()
        assert reg.get_by_name("nonexistent") == []

    def test_has(self) -> None:
        reg = MarketplaceRegistry()
        pkg = _make_pkg()
        reg.register(pkg)
        assert reg.has("pkg-1") is True
        assert reg.has("nonexistent") is False

    def test_all(self) -> None:
        reg = MarketplaceRegistry()
        pkg1 = _make_pkg(package_id="pkg-1")
        pkg2 = _make_pkg(package_id="pkg-2", name="test-tool", type_=PackageType.TOOL)
        reg.register(pkg1)
        reg.register(pkg2)
        pkgs = reg.all()
        assert len(pkgs) == 2
        assert pkg1 in pkgs
        assert pkg2 in pkgs

    def test_unregister(self) -> None:
        reg = MarketplaceRegistry()
        pkg = _make_pkg()
        reg.register(pkg)
        reg.unregister("pkg-1")
        assert reg.has("pkg-1") is False

    def test_unregister_not_found(self) -> None:
        reg = MarketplaceRegistry()
        with pytest.raises(PackageNotFoundError, match="not found"):
            reg.unregister("nonexistent")

    def test_unregister_removes_versions(self) -> None:
        reg = MarketplaceRegistry()
        pkg = _make_pkg()
        ver = _make_version()
        reg.register(pkg)
        reg.add_version(ver)
        reg.unregister("pkg-1")
        assert reg.get_versions("pkg-1") == []

    def test_search_by_query(self) -> None:
        reg = MarketplaceRegistry()
        pkg1 = _make_pkg(package_id="pkg-1", name="agent-alpha")
        pkg2 = _make_pkg(package_id="pkg-2", name="tool-beta")
        reg.register(pkg1)
        reg.register(pkg2)
        results = reg.search(query="alpha")
        assert len(results) == 1
        assert results[0] is pkg1

    def test_search_by_type(self) -> None:
        reg = MarketplaceRegistry()
        pkg1 = _make_pkg(package_id="pkg-1", name="agent", type_=PackageType.AGENT)
        pkg2 = _make_pkg(package_id="pkg-2", name="tool", type_=PackageType.TOOL)
        reg.register(pkg1)
        reg.register(pkg2)
        results = reg.search(type_filter=PackageType.TOOL)
        assert len(results) == 1
        assert results[0] is pkg2

    def test_search_by_status(self) -> None:
        reg = MarketplaceRegistry()
        pkg1 = _make_pkg(package_id="pkg-1", status=PackageStatus.DRAFT)
        pkg2 = _make_pkg(package_id="pkg-2", status=PackageStatus.PUBLISHED)
        reg.register(pkg1)
        reg.register(pkg2)
        results = reg.search(status_filter=PackageStatus.PUBLISHED)
        assert len(results) == 1
        assert results[0] is pkg2

    def test_search_by_tag(self) -> None:
        reg = MarketplaceRegistry()
        pkg1 = _make_pkg(package_id="pkg-1", tags=("ai",))
        pkg2 = _make_pkg(package_id="pkg-2", tags=("nlp",))
        reg.register(pkg1)
        reg.register(pkg2)
        results = reg.search(tag="ai")
        assert len(results) == 1
        assert results[0] is pkg1

    def test_search_combined_filters(self) -> None:
        reg = MarketplaceRegistry()
        pkg = _make_pkg(
            package_id="pkg-1",
            name="agent-alpha",
            type_=PackageType.AGENT,
            status=PackageStatus.PUBLISHED,
            tags=("ai",),
        )
        reg.register(pkg)
        results = reg.search(
            query="alpha",
            type_filter=PackageType.AGENT,
            status_filter=PackageStatus.PUBLISHED,
            tag="ai",
        )
        assert len(results) == 1

    def test_len(self) -> None:
        reg = MarketplaceRegistry()
        assert len(reg) == 0
        reg.register(_make_pkg())
        assert len(reg) == 1

    def test_contains(self) -> None:
        reg = MarketplaceRegistry()
        pkg = _make_pkg()
        reg.register(pkg)
        assert "pkg-1" in reg
        assert "nonexistent" not in reg

    def test_all_published(self) -> None:
        reg = MarketplaceRegistry()
        pkg1 = _make_pkg(package_id="pkg-1", status=PackageStatus.PUBLISHED)
        pkg2 = _make_pkg(package_id="pkg-2", status=PackageStatus.DRAFT)
        reg.register(pkg1)
        reg.register(pkg2)
        published = reg.all_published()
        assert len(published) == 1
        assert published[0] is pkg1

    def test_update_status(self) -> None:
        reg = MarketplaceRegistry()
        pkg = _make_pkg(status=PackageStatus.DRAFT)
        reg.register(pkg)
        updated = reg.update_status("pkg-1", PackageStatus.PUBLISHED)
        assert updated.status is PackageStatus.PUBLISHED
        assert reg.get("pkg-1").status is PackageStatus.PUBLISHED

    def test_update_status_not_found(self) -> None:
        reg = MarketplaceRegistry()
        with pytest.raises(PackageNotFoundError):
            reg.update_status("nonexistent", PackageStatus.PUBLISHED)

    def test_increment_downloads(self) -> None:
        reg = MarketplaceRegistry()
        pkg = _make_pkg()
        reg.register(pkg)
        updated = reg.increment_downloads("pkg-1")
        assert updated.downloads == 1
        assert reg.get("pkg-1").downloads == 1

    def test_add_and_get_versions(self) -> None:
        reg = MarketplaceRegistry()
        ver = _make_version()
        reg.add_version(ver)
        versions = reg.get_versions("pkg-1")
        assert len(versions) == 1
        assert versions[0] is ver

    def test_get_versions_empty(self) -> None:
        reg = MarketplaceRegistry()
        assert reg.get_versions("nonexistent") == []

    def test_get_latest_version(self) -> None:
        reg = MarketplaceRegistry()
        v1 = _make_version(version="1.0.0")
        v2 = _make_version(version="2.0.0")
        reg.add_version(v1)
        reg.add_version(v2)
        latest = reg.get_latest_version("pkg-1")
        assert latest is not None
        assert latest.version == "2.0.0"

    def test_get_latest_version_none(self) -> None:
        reg = MarketplaceRegistry()
        assert reg.get_latest_version("nonexistent") is None
