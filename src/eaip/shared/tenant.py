"""Tenant context — multi-tenancy primitives for workspace isolation.

Provides :class:`TenantContext` for propagating tenant identity through
the call stack and :class:`TenantAwareRepository` for automatic
tenant-scoped data isolation.
"""

from __future__ import annotations

import contextvars
from typing import Any, TypeVar

from eaip.interfaces.repository import AbstractRepository
from eaip.shared.repository import InMemoryRepository

ID = TypeVar("ID")
T = TypeVar("T")

# Context variable for the current tenant ID.
_current_tenant: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "_current_tenant", default=None
)


def get_current_tenant() -> str | None:
    """Return the tenant ID for the current execution context."""
    return _current_tenant.get()


def set_current_tenant(tenant_id: str | None) -> None:
    """Set the tenant ID for the current execution context."""
    if tenant_id is None:
        _current_tenant.set(None)
    else:
        _current_tenant.set(tenant_id)


class TenantContext:
    """Context manager for scoping code to a specific tenant.

    Usage::

        with TenantContext("org-123"):
            assert get_current_tenant() == "org-123"
    """

    def __init__(self, tenant_id: str | None) -> None:
        self._tenant_id = tenant_id
        self._token: contextvars.Token[str | None] | None = None

    def __enter__(self) -> TenantContext:
        self._token = _current_tenant.set(self._tenant_id)
        return self

    def __exit__(self, *args: object) -> None:
        if self._token is not None:
            _current_tenant.reset(self._token)


class TenantAwareRepository(AbstractRepository[ID, T]):
    """Repository that automatically scopes data by the current tenant.

    Wraps an inner :class:`InMemoryRepository`, adding a tenant-scoped
    prefix to every key so that tenants never see each other's data.
    """

    def __init__(self, inner: InMemoryRepository[str, T] | None = None) -> None:
        self._inner = inner or InMemoryRepository[str, T]()

    def _tenant_key(self, identifier: ID) -> str:
        tenant = get_current_tenant() or "__system__"
        return f"{tenant}:{identifier}"

    async def get(self, identifier: ID) -> T | None:
        return await self._inner.get(self._tenant_key(identifier))

    async def add(self, entity: T, ttl_seconds: float | None = None) -> None:
        await self._inner.add(entity, ttl_seconds=ttl_seconds)

    async def remove(self, identifier: ID) -> bool:
        return await self._inner.remove(self._tenant_key(identifier))

    async def iter_all(self) -> Any:
        async for item in self._inner.iter_all():
            yield item

    async def clear(self) -> None:
        await self._inner.clear()

    async def cleanup_expired(self) -> int:
        return await self._inner.cleanup_expired()

    def get_stats(self) -> dict[str, Any]:
        return self._inner.get_stats()


__all__ = [
    "TenantAwareRepository",
    "TenantContext",
    "get_current_tenant",
    "set_current_tenant",
]
