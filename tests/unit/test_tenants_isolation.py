"""Tests for :mod:`eaip.tenants.isolation`."""

from __future__ import annotations

import pytest

from eaip.tenants.isolation import TenantIsolationService


@pytest.fixture
def isolation() -> TenantIsolationService:
    return TenantIsolationService()


class TestTenantIsolationService:
    async def test_isolate_tenant(self, isolation: TenantIsolationService) -> None:
        result = await isolation.isolate_tenant("t-1")
        assert result["tenant_id"] == "t-1"
        assert "namespace" in result
        assert result["namespace"] == "tenant-t-1"
        assert "database" in result
        assert "cache_prefix" in result

    async def test_isolate_tenant_unique_namespace(self, isolation: TenantIsolationService) -> None:
        r1 = await isolation.isolate_tenant("t-1")
        r2 = await isolation.isolate_tenant("t-2")
        assert r1["namespace"] != r2["namespace"]

    async def test_get_isolation_level(self, isolation: TenantIsolationService) -> None:
        await isolation.isolate_tenant("t-1")
        level = await isolation.get_isolation_level("t-1")
        assert level == "namespace"

    async def test_get_isolation_level_not_found(self, isolation: TenantIsolationService) -> None:
        with pytest.raises(ValueError, match="No isolation config"):
            await isolation.get_isolation_level("nonexistent")

    async def test_configure_isolation(self, isolation: TenantIsolationService) -> None:
        await isolation.isolate_tenant("t-1")
        updated = await isolation.configure_isolation(
            "t-1", {"level": "database", "region": "us-east"}
        )
        assert updated["level"] == "database"
        assert updated["region"] == "us-east"

    async def test_configure_isolation_new_tenant(self, isolation: TenantIsolationService) -> None:
        updated = await isolation.configure_isolation(
            "t-1", {"level": "cluster", "namespace": "custom"}
        )
        assert updated["tenant_id"] == "t-1"
        assert updated["level"] == "cluster"

    async def test_validate_isolation_valid(self, isolation: TenantIsolationService) -> None:
        await isolation.isolate_tenant("t-1")
        assert await isolation.validate_isolation("t-1") is True

    async def test_validate_isolation_invalid(self, isolation: TenantIsolationService) -> None:
        await isolation.configure_isolation("t-1", {"level": "basic"})
        assert await isolation.validate_isolation("t-1") is False

    async def test_validate_isolation_not_found(self, isolation: TenantIsolationService) -> None:
        assert await isolation.validate_isolation("nonexistent") is False

    async def test_isolation_preserves_config(self, isolation: TenantIsolationService) -> None:
        await isolation.isolate_tenant("t-1")
        await isolation.configure_isolation("t-1", {"custom_key": "custom_value"})
        level = await isolation.get_isolation_level("t-1")
        assert level == "namespace"
        assert await isolation.validate_isolation("t-1") is True
