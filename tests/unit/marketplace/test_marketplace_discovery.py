from __future__ import annotations

import pytest

from eaip.marketplace.discovery import DiscoveryService
from eaip.marketplace.exceptions import PackageNotFoundError
from eaip.marketplace.models import MarketplacePackage, PackageStatus, PackageType


def _make_pkg(
    package_id: str = "pkg-1",
    name: str = "test-agent",
    type_: PackageType = PackageType.AGENT,
    status: PackageStatus = PackageStatus.PUBLISHED,
    tags: tuple[str, ...] = (),
) -> MarketplacePackage:
    return MarketplacePackage(
        package_id=package_id,
        name=name,
        type=type_,
        version="1.0.0",
        description=f"Description of {name}",
        author="developer",
        status=status,
        tags=tags,
    )


class TestDiscoveryService:
    def test_default_initialization(self) -> None:
        svc = DiscoveryService()
        assert svc.registry is not None

    def test_custom_registry(self) -> None:
        from eaip.marketplace.registry import MarketplaceRegistry

        reg = MarketplaceRegistry()
        pkg = _make_pkg()
        reg.register(pkg)
        svc = DiscoveryService(registry=reg)
        assert svc.registry is reg

    def test_discover_packages_returns_published_only(self) -> None:
        svc = DiscoveryService()
        pub = _make_pkg(package_id="pkg-1", status=PackageStatus.PUBLISHED)
        draft = _make_pkg(package_id="pkg-2", name="draft", status=PackageStatus.DRAFT)
        svc.registry.register(pub)
        svc.registry.register(draft)
        results = svc.discover_packages()
        assert len(results) == 1
        assert results[0] is pub

    def test_discover_packages_by_type(self) -> None:
        svc = DiscoveryService()
        agent = _make_pkg(package_id="pkg-1", type_=PackageType.AGENT)
        tool = _make_pkg(package_id="pkg-2", name="tool", type_=PackageType.TOOL)
        svc.registry.register(agent)
        svc.registry.register(tool)
        results = svc.discover_packages(type_filter=PackageType.TOOL)
        assert len(results) == 1
        assert results[0] is tool

    def test_discover_packages_by_tag(self) -> None:
        svc = DiscoveryService()
        pkg1 = _make_pkg(package_id="pkg-1", tags=("ai",))
        pkg2 = _make_pkg(package_id="pkg-2", name="other", tags=("nlp",))
        svc.registry.register(pkg1)
        svc.registry.register(pkg2)
        results = svc.discover_packages(tag="ai")
        assert len(results) == 1
        assert results[0] is pkg1

    def test_discover_packages_empty(self) -> None:
        svc = DiscoveryService()
        assert svc.discover_packages() == []

    def test_get_package_returns_published(self) -> None:
        svc = DiscoveryService()
        pkg = _make_pkg(status=PackageStatus.PUBLISHED)
        svc.registry.register(pkg)
        result = svc.get_package("pkg-1")
        assert result is pkg

    def test_get_package_returns_deprecated(self) -> None:
        svc = DiscoveryService()
        pkg = _make_pkg(status=PackageStatus.DEPRECATED)
        svc.registry.register(pkg)
        result = svc.get_package("pkg-1")
        assert result is pkg

    def test_get_package_raises_for_draft(self) -> None:
        svc = DiscoveryService()
        pkg = _make_pkg(status=PackageStatus.DRAFT)
        svc.registry.register(pkg)
        with pytest.raises(PackageNotFoundError, match="not available"):
            svc.get_package("pkg-1")

    def test_get_package_not_found(self) -> None:
        svc = DiscoveryService()
        with pytest.raises(PackageNotFoundError, match="not found"):
            svc.get_package("nonexistent")

    def test_search(self) -> None:
        svc = DiscoveryService()
        pkg1 = _make_pkg(package_id="pkg-1", name="agent-alpha")
        pkg2 = _make_pkg(package_id="pkg-2", name="tool-beta")
        svc.registry.register(pkg1)
        svc.registry.register(pkg2)
        results = svc.search("alpha")
        assert len(results) == 1
        assert results[0] is pkg1

    def test_search_filters_non_published(self) -> None:
        svc = DiscoveryService()
        pub = _make_pkg(package_id="pkg-1", name="agent", status=PackageStatus.PUBLISHED)
        draft = _make_pkg(package_id="pkg-2", name="agent", status=PackageStatus.DRAFT)
        svc.registry.register(pub)
        svc.registry.register(draft)
        results = svc.search("agent")
        assert len(results) == 1

    def test_search_empty(self) -> None:
        svc = DiscoveryService()
        assert svc.search("nonexistent") == []

    def test_search_with_type_filter(self) -> None:
        svc = DiscoveryService()
        pkg = _make_pkg(package_id="pkg-1", name="agent", type_=PackageType.AGENT)
        svc.registry.register(pkg)
        results = svc.search("agent", type_filter=PackageType.TOOL)
        assert results == []

    def test_search_with_tag(self) -> None:
        svc = DiscoveryService()
        pkg = _make_pkg(package_id="pkg-1", name="agent", tags=("ai",))
        svc.registry.register(pkg)
        results = svc.search("agent", tag="ai")
        assert len(results) == 1
