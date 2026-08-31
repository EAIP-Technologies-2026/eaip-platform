"""Marketplace experience — browse, publish, and install packages.

Surfaces the existing marketplace subsystem (DiscoveryService, Publisher,
PackageManager) over HTTP instead of returning placeholder data.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from weakref import WeakKeyDictionary

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.http.dependencies import get_current_user
from eaip.logging.context import get_logger
from eaip.marketplace.discovery import DiscoveryService
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
from eaip.marketplace.publisher import Publisher
from eaip.marketplace.registry import MarketplaceRegistry

router = APIRouter(
    prefix="/marketplace", tags=["marketplace"], dependencies=[Depends(get_current_user)]
)
log = get_logger("eaip.http.routers.marketplace")

_FALLBACK_REGISTRY = MarketplaceRegistry()
_FALLBACK_DISCOVERY: DiscoveryService | None = None
_FALLBACK_MANAGER: PackageManager | None = None
_FALLBACK_PUBLISHER: Publisher | None = None
_CORE_CACHE: "WeakKeyDictionary[MarketplaceRegistry, tuple[DiscoveryService, PackageManager, Publisher]]" = WeakKeyDictionary()

# Category ids map onto package types so the catalog stays data-driven.
CATEGORY_TYPES: dict[str, PackageType] = {
    "agent-packs": PackageType.AGENT,
    "tool-packs": PackageType.TOOL,
    "plugin-packs": PackageType.PLUGIN,
    "templates": PackageType.TEMPLATE,
    "adapters": PackageType.ADAPTER,
}

CATEGORY_NAMES: dict[str, str] = {
    "agent-packs": "Agent Packs",
    "tool-packs": "Tool Packs",
    "plugin-packs": "Plugin Packs",
    "templates": "Templates",
    "adapters": "Adapters",
}


def _container(request: Request) -> Any:
    return request.app.state.lifecycle.platform.container


def _fallback_core() -> tuple[DiscoveryService, PackageManager, Publisher]:
    """Lazily build a stable set of marketplace services for un-wired harnesses."""
    global _FALLBACK_DISCOVERY, _FALLBACK_MANAGER, _FALLBACK_PUBLISHER
    if _FALLBACK_DISCOVERY is None:
        _FALLBACK_DISCOVERY = DiscoveryService(registry=_FALLBACK_REGISTRY)
    if _FALLBACK_MANAGER is None:
        _FALLBACK_MANAGER = PackageManager(registry=_FALLBACK_REGISTRY)
    if _FALLBACK_PUBLISHER is None:
        _FALLBACK_PUBLISHER = Publisher(registry=_FALLBACK_REGISTRY)
    return _FALLBACK_DISCOVERY, _FALLBACK_MANAGER, _FALLBACK_PUBLISHER


def _core(request: Request) -> tuple[DiscoveryService, PackageManager, Publisher]:
    """Resolve the marketplace services, sharing one registry in all cases.

    The container is fully wired via __main__ in production. When any service
    is missing the remaining pieces are built from the same registry so browse,
    publish, and install always agree.
    """
    container = _container(request)
    discovery = container.try_resolve(DiscoveryService)
    manager = container.try_resolve(PackageManager)
    publisher = container.try_resolve(Publisher)

    if discovery is not None and manager is not None and publisher is not None:
        return discovery, manager, publisher

    registry = container.try_resolve(MarketplaceRegistry)
    if registry is None:
        return _fallback_core()

    cached = _CORE_CACHE.get(registry)
    if cached is not None:
        return cached

    core = (
        discovery if discovery is not None else DiscoveryService(registry=registry),
        manager if manager is not None else PackageManager(registry=registry),
        publisher if publisher is not None else Publisher(registry=registry),
    )
    _CORE_CACHE[registry] = core
    return core


def _package_to_dict(pkg: MarketplacePackage) -> dict[str, Any]:
    return {
        "id": pkg.package_id,
        "name": pkg.name,
        "type": pkg.type.value,
        "version": pkg.version,
        "description": pkg.description,
        "author": pkg.author,
        "downloads": pkg.downloads,
        "rating": pkg.rating,
        "tags": list(pkg.tags),
        "dependencies": list(pkg.dependencies),
        "status": pkg.status.value,
        "createdAt": pkg.created_at.isoformat(),
        "updatedAt": pkg.updated_at.isoformat(),
    }


def _installation_to_dict(inst: Any) -> dict[str, Any]:
    return {
        "id": inst.installation_id,
        "packageId": inst.package_id,
        "version": inst.version,
        "installedAt": inst.installed_at.isoformat(),
        "installedBy": inst.installed_by,
        "status": inst.status,
    }


def _ensure_installable_version(registry: MarketplaceRegistry, package: MarketplacePackage) -> None:
    """Ensure an installable PackageVersion exists for a package.

    Packages published through the router carry their own version field. When
    the registry has no version records yet, derive one from the package so the
    PackageManager lifecycle stays consistent.
    """
    if registry.get_versions(package.package_id):
        return
    registry.add_version(
        PackageVersion(
            package_id=package.package_id,
            version=package.version,
            semver_range=f">={package.version}",
            changelog=f"Initial version {package.version}",
            checksum="",
            size_bytes=0,
            is_compatible=True,
        )
    )


@router.get("/search")
async def marketplace_search(
    request: Request, search: str = "", category: str = "", tags: str = "", sort: str = "", page: int = 1, pageSize: int = 20
):
    discovery, _, _ = _core(request)
    type_filter = CATEGORY_TYPES.get(category)
    tag = category if category and type_filter is None else (tags.split(",")[0].strip() if tags else None)
    query = search.strip() or None
    if query:
        results = discovery.search(query, type_filter=type_filter, tag=tag)
    else:
        results = discovery.discover_packages(type_filter=type_filter, tag=tag)
    if sort == "rating":
        results = sorted(results, key=lambda p: p.rating, reverse=True)
    elif sort == "downloads":
        results = sorted(results, key=lambda p: p.downloads, reverse=True)
    total = len(results)
    page = max(1, int(page))
    page_size = min(100, max(1, int(pageSize)))
    start = (page - 1) * page_size
    sliced = results[start : start + page_size]
    return {"packages": [_package_to_dict(p) for p in sliced], "total": total, "page": page, "pageSize": page_size}


@router.get("/recommendations")
async def marketplace_recommendations(request: Request):
    discovery, _, _ = _core(request)
    try:
        all_pkgs = discovery.discover_packages(tag="featured")
        if not all_pkgs:
            all_pkgs = discovery.discover_packages()[:5]
        return {"packages": [_package_to_dict(p) for p in all_pkgs[:5]], "reason": "recommended for your organization"}
    except Exception:
        return {"packages": [], "reason": "no recommendations"}


@router.get("/packages")
async def list_packages(
    request: Request, search: str = "", category: str = "", page: int = 1, pageSize: int = 20
):
    discovery, _, _ = _core(request)
    type_filter = CATEGORY_TYPES.get(category)
    tag = category if category and type_filter is None else None

    query = search.strip() or None
    if query:
        results = discovery.search(query, type_filter=type_filter, tag=tag)
    else:
        results = discovery.discover_packages(type_filter=type_filter, tag=tag)

    total = len(results)
    page = max(1, int(page))
    page_size = min(100, max(1, int(pageSize)))
    start = (page - 1) * page_size
    sliced = results[start : start + page_size]

    return {
        "packages": [_package_to_dict(p) for p in sliced],
        "total": total,
        "page": page,
        "pageSize": page_size,
    }


@router.get("/packages/featured")
async def featured_packages(request: Request):
    discovery, _, _ = _core(request)
    results = discovery.discover_packages(tag="featured")
    return {"packages": [_package_to_dict(p) for p in results]}


@router.get("/packages/{package_id}")
async def get_package(request: Request, package_id: str):
    discovery, _, _ = _core(request)
    try:
        pkg = discovery.get_package(package_id)
    except PackageNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _package_to_dict(pkg)


@router.post("/packages")
async def create_package(
    request: Request, body: dict[str, Any], _user: dict[str, Any] = Depends(get_current_user)
):
    name = str(body.get("name", "")).strip()
    if not name:
        raise HTTPException(status_code=400, detail="Package name is required")

    type_name = str(body.get("type", "template")).strip()
    try:
        pkg_type = PackageType(type_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid package type: {type_name!r}") from exc

    author = str(
        _user.get("name", _user.get("preferred_username", _user.get("sub", "unknown")))
    )
    package_id = f"pkg-{uuid.uuid4().hex[:8]}"
    package = MarketplacePackage(
        package_id=package_id,
        name=name,
        type=pkg_type,
        version=str(body.get("version", "1.0.0")).strip() or "1.0.0",
        description=str(body.get("description", "")).strip(),
        author=author,
        tags=tuple(str(t).strip() for t in body.get("tags", []) if str(t).strip()),
        status=PackageStatus.PUBLISHED,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    discovery, _, publisher = _core(request)
    published = await publisher.publish(package)
    _ensure_installable_version(discovery.registry, published)

    log.info("marketplace.http.package_created", package_id=package_id, name=name)
    return {"id": package_id, "name": name, "status": PackageStatus.PUBLISHED.value}


@router.get("/installations")
async def list_installations(request: Request):
    _, manager, _ = _core(request)
    return [_installation_to_dict(inst) for inst in manager.list_installations()]


@router.post("/packages/{package_id}/install")
async def install_package(
    request: Request, package_id: str, _user: dict[str, Any] = Depends(get_current_user)
):
    _, manager, _ = _core(request)
    try:
        try:
            pkg = manager.registry.get(package_id)
            _ensure_installable_version(manager.registry, pkg)
        except PackageNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

        actor = str(
            _user.get("name", _user.get("preferred_username", _user.get("sub", "system")))
        )
        installation = await manager.install(package_id, installed_by=actor)
    except PackageAlreadyInstalledError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except PackageNotCompatibleError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DependencyNotSatisfiedError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log.info("marketplace.http.package_installed", package_id=package_id)
    return {"status": "installed", "id": installation.installation_id}


@router.post("/packages/{package_id}/uninstall")
async def uninstall_package(
    request: Request, package_id: str, _user: dict[str, Any] = Depends(get_current_user)
):
    _, manager, _ = _core(request)
    active = [
        inst for inst in manager.list_installations(package_id=package_id) if inst.status == "active"
    ]
    if not active:
        raise HTTPException(
            status_code=404, detail=f"No active installation for package {package_id!r}"
        )
    for inst in active:
        await manager.uninstall(inst.installation_id)

    log.info("marketplace.http.package_uninstalled", package_id=package_id)
    return {"status": "uninstalled"}


@router.get("/categories")
async def list_categories(request: Request):
    discovery, _, _ = _core(request)
    categories = []
    for category_id, pkg_type in CATEGORY_TYPES.items():
        count = len(discovery.discover_packages(type_filter=pkg_type))
        categories.append(
            {"id": category_id, "name": CATEGORY_NAMES.get(category_id, category_id), "count": count}
        )
    return {"categories": categories}


@router.get("/packages/{package_id}/detail")
async def package_detail(request: Request, package_id: str):
    discovery, _, _ = _core(request)
    try:
        pkg = discovery.get_package(package_id)
    except PackageNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    data = _package_to_dict(pkg)
    caps = getattr(pkg, "capabilities", None)
    reqs = getattr(pkg, "requirements", None)
    compat = getattr(pkg, "compatibility", None)
    data["capabilities"] = list(caps) if caps else list(pkg.tags)
    data["requirements"] = list(reqs) if reqs else []
    data["compatibility"] = list(compat) if compat else []
    data["installable"] = pkg.status == PackageStatus.PUBLISHED
    return data


@router.post("/packages/{package_id}/configure")
async def configure_package(request: Request, package_id: str, body: dict[str, Any], _user: dict = Depends(get_current_user)):
    discovery, _, _ = _core(request)
    try:
        pkg = discovery.get_package(package_id)
    except PackageNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    config = body.get("config") or body.get("configuration") or body
    return {"package_id": package_id, "name": pkg.name, "config": config, "status": "configured"}


@router.post("/packages/{package_id}/disable")
async def disable_package(request: Request, package_id: str, _user: dict = Depends(get_current_user)):
    _, manager, _ = _core(request)
    active = [i for i in manager.list_installations(package_id=package_id) if i.status == "active"]
    if not active:
        raise HTTPException(status_code=404, detail=f"No active installation for {package_id!r}")
    for inst in active:
        manager._installations[inst.installation_id] = inst.model_copy(update={"status": "disabled"})
    return {"status": "disabled", "package_id": package_id}


@router.post("/packages/{package_id}/enable")
async def enable_package(request: Request, package_id: str, _user: dict = Depends(get_current_user)):
    _, manager, _ = _core(request)
    disabled = [i for i in manager.list_installations(package_id=package_id) if i.status == "disabled"]
    if not disabled:
        raise HTTPException(status_code=404, detail=f"No disabled installation for {package_id!r}")
    for inst in disabled:
        manager._installations[inst.installation_id] = inst.model_copy(update={"status": "active"})
    return {"status": "enabled", "package_id": package_id}
