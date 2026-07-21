"""Tenant isolation service — resource isolation tracking and validation."""

from __future__ import annotations

from typing import Any

from eaip.logging.context import get_logger


class TenantIsolationService:
    """Manages and validates tenant isolation boundaries.

    In-memory isolation tracking that simulates per-tenant resource
    isolation (separate databases, caches, namespaces, etc.).
    """

    def __init__(self) -> None:
        self._log = get_logger("eaip.tenants.isolation")
        self._isolation_configs: dict[str, dict[str, Any]] = {}

    async def isolate_tenant(self, tenant_id: str) -> dict[str, Any]:
        """Create isolated resources for a tenant.

        Returns:
            A dictionary describing the isolation configuration created.
        """
        isolation = {
            "tenant_id": tenant_id,
            "namespace": f"tenant-{tenant_id}",
            "database": f"db_{tenant_id}",
            "cache_prefix": f"tenant:{tenant_id}",
            "storage_container": f"tenant-{tenant_id}-data",
            "level": "namespace",
        }
        self._isolation_configs[tenant_id] = isolation
        self._log.info("tenant.isolation_created", tenant_id=tenant_id)
        return isolation

    async def get_isolation_level(self, tenant_id: str) -> str:
        """Get the isolation level for a tenant.

        Returns:
            The isolation level string (e.g. 'namespace', 'database', 'cluster').

        Raises:
            ValueError: If the tenant has no isolation configuration.
        """
        config = self._isolation_configs.get(tenant_id)
        if config is None:
            raise ValueError(f"No isolation config for tenant {tenant_id!r}")
        return str(config.get("level", "namespace"))

    async def configure_isolation(self, tenant_id: str, config: dict[str, Any]) -> dict[str, Any]:
        """Configure isolation for a tenant.

        Args:
            tenant_id: The tenant identifier.
            config: Isolation configuration parameters.

        Returns:
            The updated isolation configuration.
        """
        current = self._isolation_configs.get(tenant_id, {})
        current.update(config)
        current["tenant_id"] = tenant_id
        self._isolation_configs[tenant_id] = current
        self._log.info("tenant.isolation_configured", tenant_id=tenant_id)
        return current

    async def validate_isolation(self, tenant_id: str) -> bool:
        """Validate isolation boundaries for a tenant.

        Returns:
            True if isolation is properly configured, False otherwise.
        """
        config = self._isolation_configs.get(tenant_id)
        if config is None:
            return False
        required_keys = {"namespace", "database", "cache_prefix"}
        return required_keys.issubset(config.keys())
