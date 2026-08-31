from __future__ import annotations

import pytest

from eaip.marketplace.exceptions import PackageNotCompatibleError, PackageNotFoundError
from eaip.marketplace.models import (
    MarketplacePackage,
    PackageStatus,
    PackageType,
)
from eaip.marketplace.publisher import Publisher


def _make_pkg(
    package_id: str | None = "pkg-1",
    name: str = "test-agent",
    status: PackageStatus = PackageStatus.DRAFT,
    metadata: dict[str, str] | None = None,
) -> MarketplacePackage:
    return MarketplacePackage(
        package_id=package_id,
        name=name,
        type=PackageType.AGENT,
        version="1.0.0",
        description=f"Description of {name}",
        author="developer",
        status=status,
        metadata=metadata or {},
    )


class TestPublisher:
    def test_default_initialization(self) -> None:
        pub = Publisher()
        assert pub.registry is not None

    def test_custom_registry(self) -> None:
        from eaip.marketplace.registry import MarketplaceRegistry

        reg = MarketplaceRegistry()
        pkg = _make_pkg()
        reg.register(pkg)
        pub = Publisher(registry=reg)
        assert pub.registry is reg

    @pytest.mark.asyncio
    async def test_publish(self) -> None:
        pub = Publisher()
        pkg = _make_pkg()
        result = await pub.publish(pkg)
        assert result.package_id == "pkg-1"
        assert pub.registry.has("pkg-1")

    @pytest.mark.asyncio
    async def test_publish_auto_assigns_id(self) -> None:
        pub = Publisher()
        pkg = _make_pkg(package_id="")
        result = await pub.publish(pkg)
        assert result.package_id is not None
        assert result.package_id != ""

    @pytest.mark.asyncio
    async def test_update_name(self) -> None:
        pub = Publisher()
        pkg = _make_pkg()
        await pub.publish(pkg)
        updated = await pub.update("pkg-1", name="new-name")
        assert updated.name == "new-name"

    @pytest.mark.asyncio
    async def test_update_description(self) -> None:
        pub = Publisher()
        pkg = _make_pkg()
        await pub.publish(pkg)
        updated = await pub.update("pkg-1", description="New description")
        assert updated.description == "New description"

    @pytest.mark.asyncio
    async def test_update_version(self) -> None:
        pub = Publisher()
        pkg = _make_pkg()
        await pub.publish(pkg)
        updated = await pub.update("pkg-1", version="2.0.0")
        assert updated.version == "2.0.0"

    @pytest.mark.asyncio
    async def test_update_tags(self) -> None:
        pub = Publisher()
        pkg = _make_pkg()
        await pub.publish(pkg)
        updated = await pub.update("pkg-1", tags=("ai", "nlp"))
        assert updated.tags == ("ai", "nlp")

    @pytest.mark.asyncio
    async def test_update_metadata_merges(self) -> None:
        pub = Publisher()
        pkg = _make_pkg(metadata={"existing": "val"})
        await pub.publish(pkg)
        updated = await pub.update("pkg-1", metadata={"new": "value"})
        assert updated.metadata["existing"] == "val"
        assert updated.metadata["new"] == "value"

    @pytest.mark.asyncio
    async def test_update_no_changes_returns_existing(self) -> None:
        pub = Publisher()
        pkg = _make_pkg()
        await pub.publish(pkg)
        updated = await pub.update("pkg-1")
        assert updated is pub.registry.get("pkg-1")

    @pytest.mark.asyncio
    async def test_update_not_found(self) -> None:
        pub = Publisher()
        with pytest.raises(PackageNotFoundError, match="not found"):
            await pub.update("nonexistent", name="new")

    @pytest.mark.asyncio
    async def test_deprecate(self) -> None:
        pub = Publisher()
        pkg = _make_pkg()
        await pub.publish(pkg)
        updated = await pub.deprecate("pkg-1", reason="no longer supported")
        assert updated.status is PackageStatus.DEPRECATED

    @pytest.mark.asyncio
    async def test_deprecate_default_reason(self) -> None:
        pub = Publisher()
        pkg = _make_pkg()
        await pub.publish(pkg)
        updated = await pub.deprecate("pkg-1")
        assert updated.status is PackageStatus.DEPRECATED

    @pytest.mark.asyncio
    async def test_deprecate_not_found(self) -> None:
        pub = Publisher()
        with pytest.raises(PackageNotFoundError, match="not found"):
            await pub.deprecate("nonexistent")

    @pytest.mark.asyncio
    async def test_deprecate_already_deprecated(self) -> None:
        pub = Publisher()
        pkg = _make_pkg(status=PackageStatus.DEPRECATED)
        await pub.publish(pkg)
        with pytest.raises(PackageNotCompatibleError, match="already deprecated"):
            await pub.deprecate("pkg-1")
