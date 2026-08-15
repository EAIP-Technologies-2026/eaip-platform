"""Tests for the marketplace experience — real catalog browse, publish, and install."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

from eaip.marketplace.registry import MarketplaceRegistry

from eaip.http.routers.marketplace_routes import (
    CATEGORY_TYPES,
    _ensure_installable_version,
    _installation_to_dict,
    _package_to_dict,
    create_package,
    featured_packages,
    get_package,
    install_package,
    list_categories,
    list_installations,
    list_packages,
    uninstall_package,
)


class FakeContainer:
    def __init__(self, *instances: Any) -> None:
        self._instances = list(instances)

    def try_resolve(self, cls: type) -> Any:
        for inst in self._instances:
            if isinstance(inst, cls):
                return inst
        return None


class FakeRequest:
    def __init__(self, *instances: Any) -> None:
        state = SimpleNamespace(
            lifecycle=SimpleNamespace(platform=SimpleNamespace(container=FakeContainer(*instances)))
        )
        self.app = SimpleNamespace(state=state)


USER = {"sub": "user-1", "name": "Alice"}


@pytest.mark.asyncio
async def test_empty_catalog() -> None:
    registry = MarketplaceRegistry()
    req = FakeRequest(registry)
    result = await list_packages(req)
    assert result["packages"] == []
    assert result["total"] == 0


@pytest.mark.asyncio
async def test_publish_then_discover_roundtrip() -> None:
    registry = MarketplaceRegistry()
    req = FakeRequest(registry)
    created = await create_package(req, {"name": "Demo Agent", "type": "agent"}, _user=USER)
    assert created["status"] == "published"
    assert created["id"].startswith("pkg-")

    listing = await list_packages(req)
    assert listing["total"] == 1
    assert listing["packages"][0]["name"] == "Demo Agent"
    assert listing["packages"][0]["type"] == "agent"

    detail = await get_package(req, created["id"])
    assert detail["id"] == created["id"]
    assert detail["author"] == "Alice"


@pytest.mark.asyncio
async def test_create_package_validations() -> None:
    registry = MarketplaceRegistry()
    req = FakeRequest(registry)
    with pytest.raises(HTTPException) as exc:
        await create_package(req, {"type": "agent"}, _user=USER)
    assert exc.value.status_code == 400

    with pytest.raises(HTTPException) as exc:
        await create_package(req, {"name": "X", "type": "bogus"}, _user=USER)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_get_package_not_found() -> None:
    req = FakeRequest(MarketplaceRegistry())
    with pytest.raises(HTTPException) as exc:
        await get_package(req, "missing")
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_featured_packages_by_tag() -> None:
    registry = MarketplaceRegistry()
    req = FakeRequest(registry)
    await create_package(req, {"name": "Featured One", "type": "tool", "tags": ["featured"]}, _user=USER)
    await create_package(req, {"name": "Plain One", "type": "tool"}, _user=USER)

    featured = await featured_packages(req)
    assert [p["name"] for p in featured["packages"]] == ["Featured One"]


@pytest.mark.asyncio
async def test_category_filter_and_counts() -> None:
    registry = MarketplaceRegistry()
    req = FakeRequest(registry)
    await create_package(req, {"name": "Agent Pack", "type": "agent"}, _user=USER)
    await create_package(req, {"name": "Tool Pack", "type": "tool"}, _user=USER)

    agents = await list_packages(req, category="agent-packs")
    assert agents["total"] == 1
    assert agents["packages"][0]["name"] == "Agent Pack"

    tools = await list_packages(req, category="tool-packs")
    assert tools["total"] == 1

    categories = await list_categories(req)
    by_id = {c["id"]: c for c in categories["categories"]}
    assert by_id["agent-packs"]["count"] == 1
    assert by_id["tool-packs"]["count"] == 1
    assert by_id["templates"]["count"] == 0


@pytest.mark.asyncio
async def test_search_query() -> None:
    registry = MarketplaceRegistry()
    req = FakeRequest(registry)
    await create_package(req, {"name": "Slack Connector", "type": "plugin"}, _user=USER)
    await create_package(req, {"name": "Teams Connector", "type": "plugin"}, _user=USER)

    results = await list_packages(req, search="slack")
    assert results["total"] == 1
    assert results["packages"][0]["name"] == "Slack Connector"


@pytest.mark.asyncio
async def test_pagination() -> None:
    registry = MarketplaceRegistry()
    req = FakeRequest(registry)
    for i in range(5):
        await create_package(req, {"name": f"Package {i}", "type": "agent"}, _user=USER)

    page1 = await list_packages(req, page=1, pageSize=2)
    assert len(page1["packages"]) == 2
    assert page1["total"] == 5
    assert page1["page"] == 1

    page3 = await list_packages(req, page=3, pageSize=2)
    assert len(page3["packages"]) == 1

    out_of_range = await list_packages(req, page=9, pageSize=2)
    assert out_of_range["packages"] == []


@pytest.mark.asyncio
async def test_install_uninstall_flow() -> None:
    registry = MarketplaceRegistry()
    req = FakeRequest(registry)
    created = await create_package(req, {"name": "Installable", "type": "agent"}, _user=USER)

    installed = await install_package(req, created["id"], _user=USER)
    assert installed["status"] == "installed"

    installations = await list_installations(req)
    assert len(installations) == 1
    assert installations[0]["packageId"] == created["id"]
    assert installations[0]["status"] == "active"
    assert installations[0]["installedBy"] == "Alice"

    with pytest.raises(HTTPException) as exc:
        await install_package(req, created["id"], _user=USER)
    assert exc.value.status_code == 409

    uninstalled = await uninstall_package(req, created["id"], _user=USER)
    assert uninstalled["status"] == "uninstalled"
    assert len(await list_installations(req)) == 1
    assert (await list_installations(req))[0]["status"] == "uninstalled"


@pytest.mark.asyncio
async def test_install_unknown_package_404() -> None:
    req = FakeRequest(MarketplaceRegistry())
    with pytest.raises(HTTPException) as exc:
        await install_package(req, "missing", _user=USER)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_uninstall_without_installation_404() -> None:
    registry = MarketplaceRegistry()
    req = FakeRequest(registry)
    created = await create_package(req, {"name": "Never Installed", "type": "agent"}, _user=USER)
    with pytest.raises(HTTPException) as exc:
        await uninstall_package(req, created["id"], _user=USER)
    assert exc.value.status_code == 404


def test_package_to_dict_mapping() -> None:
    from eaip.marketplace.models import MarketplacePackage, PackageStatus, PackageType

    pkg = MarketplacePackage(
        package_id="pkg-1",
        name="Sample",
        type=PackageType.AGENT,
        version="1.2.0",
        description="desc",
        author="dev",
        tags=("a", "b"),
        downloads=7,
        rating=4.5,
        status=PackageStatus.PUBLISHED,
    )
    d = _package_to_dict(pkg)
    assert d["id"] == "pkg-1"
    assert d["type"] == "agent"
    assert d["tags"] == ["a", "b"]
    assert d["status"] == "published"
    assert d["createdAt"]


def test_ensure_installable_version_adds_and_is_idempotent() -> None:
    from eaip.marketplace.models import MarketplacePackage, PackageType

    registry = MarketplaceRegistry()
    pkg = MarketplacePackage(
        package_id="pkg-v", name="V", type=PackageType.TOOL, version="3.0.0",
        description="", author="dev",
    )
    registry.register(pkg)
    assert registry.get_versions("pkg-v") == []
    _ensure_installable_version(registry, pkg)
    assert len(registry.get_versions("pkg-v")) == 1
    assert registry.get_versions("pkg-v")[0].version == "3.0.0"
    _ensure_installable_version(registry, pkg)
    assert len(registry.get_versions("pkg-v")) == 1


def test_installation_to_dict() -> None:
    from eaip.marketplace.models import PackageInstallation

    inst = PackageInstallation(
        installation_id="inst-1",
        package_id="pkg-1",
        version="1.0.0",
        installed_by="Alice",
        status="active",
    )
    d = _installation_to_dict(inst)
    assert d["id"] == "inst-1"
    assert d["packageId"] == "pkg-1"
    assert d["status"] == "active"


def test_category_types_alignment() -> None:
    from eaip.marketplace.models import PackageType

    assert set(CATEGORY_TYPES.values()) <= set(PackageType)


__all__: list[str] = []
