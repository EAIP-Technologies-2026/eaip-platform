"""Tenant-isolated marketplace registry."""

from __future__ import annotations

from typing import Any

from eaip.marketplace.exceptions import PackageNotFoundError
from eaip.marketplace.extended_models import ExtendedMarketplacePackage, Visibility
from eaip.marketplace.models import MarketplacePackage, PackageStatus, PackageType
from eaip.marketplace.registry import MarketplaceRegistry


class TenantMarketplaceRegistry:
    """Wraps :class:`MarketplaceRegistry` with tenant isolation.

    Visibility rule:
      - A package is visible to tenant ``t`` if ``package.tenant_id == t``
        OR ``package.visibility == Visibility.PUBLIC`` (or base packages
        which have no visibility field are treated as public).
    """

    def __init__(self, registry: MarketplaceRegistry | None = None) -> None:
        self._registry = registry if registry is not None else MarketplaceRegistry()

    @property
    def registry(self) -> MarketplaceRegistry:
        return self._registry

    def _is_visible(self, pkg: Any, tenant_id: str) -> bool:
        vis = getattr(pkg, "visibility", None)
        tid = getattr(pkg, "tenant_id", None)
        # Base MarketplacePackage (no tenant_id/visibility) is considered public
        if tid is None and vis is None:
            return True
        if tid is not None and tid == tenant_id:
            return True
        if vis is not None:
            try:
                if vis == Visibility.PUBLIC or str(vis) == "public":
                    return True
            except Exception:
                pass
            # StrEnum comparison also handles string
            if str(vis).lower() == "public":
                return True
        return False

    def _filtered(self, tenant_id: str) -> list[MarketplacePackage]:
        return [p for p in self._registry.all() if self._is_visible(p, tenant_id)]

    # ── tenant-scoped operations ────────────────────────────────────

    def list_for_tenant(
        self,
        tenant_id: str,
        *,
        type_filter: PackageType | None = None,
        status_filter: PackageStatus | None = None,
        tag: str | None = None,
    ) -> list[MarketplacePackage]:
        """List packages visible to *tenant_id* with optional filters."""
        results = self._filtered(tenant_id)
        if type_filter is not None:
            results = [p for p in results if p.type is type_filter]
        if status_filter is not None:
            results = [p for p in results if p.status is status_filter]
        if tag is not None:
            results = [p for p in results if tag in p.tags]
        return results

    def search_for_tenant(
        self,
        tenant_id: str,
        query: str | None = None,
        *,
        type_filter: PackageType | None = None,
        status_filter: PackageStatus | None = None,
        tag: str | None = None,
    ) -> list[MarketplacePackage]:
        """Search packages visible to *tenant_id*.

        Filtering is applied after tenant isolation so that private packages
        of other tenants never leak via search queries.
        """
        results = self._filtered(tenant_id)
        if query:
            q = query.lower()
            results = [p for p in results if q in p.name.lower() or q in p.description.lower()]
        if type_filter is not None:
            results = [p for p in results if p.type is type_filter]
        if status_filter is not None:
            results = [p for p in results if p.status is status_filter]
        if tag is not None:
            results = [p for p in results if tag in p.tags]
        return results

    def get_for_tenant(self, package_id: str, tenant_id: str) -> MarketplacePackage:
        """Return *package_id* if visible to *tenant_id*, else raise PackageNotFoundError."""
        try:
            pkg = self._registry.get(package_id)
        except PackageNotFoundError:
            raise
        if not self._is_visible(pkg, tenant_id):
            raise PackageNotFoundError(f"Package {package_id!r} not found for tenant {tenant_id!r}")
        return pkg

    # ── delegation helpers ──────────────────────────────────────────

    def register(self, package: MarketplacePackage | ExtendedMarketplacePackage) -> None:
        self._registry.register(package)  # type: ignore[arg-type]

    def has(self, package_id: str) -> bool:
        return self._registry.has(package_id)

    def __len__(self) -> int:
        return len(self._registry)

    def __contains__(self, package_id: str) -> bool:
        return package_id in self._registry


__all__ = ["TenantMarketplaceRegistry"]
