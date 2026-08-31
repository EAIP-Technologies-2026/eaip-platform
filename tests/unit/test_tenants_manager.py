"""Tests for :mod:`eaip.tenants.manager`."""

from __future__ import annotations

import pytest

from eaip.tenants.exceptions import (
    TenantNotFoundError,
    TenantSuspendedError,
    UserNotFoundError,
)
from eaip.tenants.manager import TenantManager
from eaip.tenants.models import (
    Tenant,
    TenantQuota,
    TenantStatus,
    TenantUser,
)


@pytest.fixture
def manager() -> TenantManager:
    return TenantManager()


@pytest.fixture
def sample_tenant() -> Tenant:
    return Tenant(id="t-1", name="Acme", slug="acme")


@pytest.fixture
def sample_user() -> TenantUser:
    return TenantUser(id="u-1", tenant_id="t-1", email="user@acme.com")


class TestTenantManager:
    async def test_create_tenant(self, manager: TenantManager) -> None:
        tenant = Tenant(id="t-1", name="Acme", slug="acme")
        result = await manager.create_tenant(tenant)
        assert result.id == "t-1"
        assert result.name == "Acme"

    async def test_create_duplicate_raises(self, manager: TenantManager) -> None:
        tenant = Tenant(id="t-1", name="Acme", slug="acme")
        await manager.create_tenant(tenant)
        with pytest.raises(ValueError, match="already exists"):
            await manager.create_tenant(tenant)

    async def test_get_tenant(self, manager: TenantManager, sample_tenant: Tenant) -> None:
        await manager.create_tenant(sample_tenant)
        result = await manager.get_tenant("t-1")
        assert result.id == "t-1"
        assert result.name == "Acme"

    async def test_get_tenant_not_found(self, manager: TenantManager) -> None:
        with pytest.raises(TenantNotFoundError):
            await manager.get_tenant("nonexistent")

    async def test_update_tenant(self, manager: TenantManager, sample_tenant: Tenant) -> None:
        await manager.create_tenant(sample_tenant)
        updated = await manager.update_tenant("t-1", {"name": "Acme Updated"})
        assert updated.name == "Acme Updated"
        result = await manager.get_tenant("t-1")
        assert result.name == "Acme Updated"

    async def test_update_tenant_not_found(self, manager: TenantManager) -> None:
        with pytest.raises(TenantNotFoundError):
            await manager.update_tenant("nonexistent", {"name": "X"})

    async def test_suspend_tenant(self, manager: TenantManager, sample_tenant: Tenant) -> None:
        await manager.create_tenant(sample_tenant)
        suspended = await manager.suspend_tenant("t-1")
        assert suspended.status is TenantStatus.SUSPENDED

    async def test_suspend_closed_tenant_raises(self, manager: TenantManager) -> None:
        tenant = Tenant(id="t-1", name="A", slug="a", status=TenantStatus.CLOSED)
        await manager.create_tenant(tenant)
        with pytest.raises(TenantSuspendedError, match="Cannot suspend a closed tenant"):
            await manager.suspend_tenant("t-1")

    async def test_activate_tenant(self, manager: TenantManager, sample_tenant: Tenant) -> None:
        await manager.create_tenant(sample_tenant)
        await manager.suspend_tenant("t-1")
        activated = await manager.activate_tenant("t-1")
        assert activated.status is TenantStatus.ACTIVE

    async def test_activate_closed_tenant_raises(self, manager: TenantManager) -> None:
        tenant = Tenant(id="t-1", name="A", slug="a", status=TenantStatus.CLOSED)
        await manager.create_tenant(tenant)
        with pytest.raises(TenantSuspendedError, match="Cannot activate a closed tenant"):
            await manager.activate_tenant("t-1")

    async def test_close_tenant(self, manager: TenantManager, sample_tenant: Tenant) -> None:
        await manager.create_tenant(sample_tenant)
        closed = await manager.close_tenant("t-1")
        assert closed.status is TenantStatus.CLOSED

    async def test_list_tenants_all(self, manager: TenantManager) -> None:
        t1 = Tenant(id="t-1", name="A", slug="a")
        t2 = Tenant(id="t-2", name="B", slug="b")
        await manager.create_tenant(t1)
        await manager.create_tenant(t2)
        result = await manager.list_tenants()
        assert len(result) == 2

    async def test_list_tenants_filter_by_status(self, manager: TenantManager) -> None:
        t1 = Tenant(id="t-1", name="A", slug="a", status=TenantStatus.ACTIVE)
        t2 = Tenant(id="t-2", name="B", slug="b", status=TenantStatus.SUSPENDED)
        await manager.create_tenant(t1)
        await manager.create_tenant(t2)
        result = await manager.list_tenants(status=TenantStatus.ACTIVE)
        assert len(result) == 1
        assert result[0].id == "t-1"

    async def test_list_tenants_empty(self, manager: TenantManager) -> None:
        result = await manager.list_tenants()
        assert result == []

    async def test_add_user(
        self, manager: TenantManager, sample_tenant: Tenant, sample_user: TenantUser
    ) -> None:
        await manager.create_tenant(sample_tenant)
        result = await manager.add_user("t-1", sample_user)
        assert result.id == "u-1"

    async def test_add_user_to_suspended_tenant_raises(
        self, manager: TenantManager, sample_user: TenantUser
    ) -> None:
        tenant = Tenant(id="t-1", name="A", slug="a", status=TenantStatus.SUSPENDED)
        await manager.create_tenant(tenant)
        with pytest.raises(TenantSuspendedError, match="suspended"):
            await manager.add_user("t-1", sample_user)

    async def test_add_duplicate_user_raises(
        self, manager: TenantManager, sample_tenant: Tenant, sample_user: TenantUser
    ) -> None:
        await manager.create_tenant(sample_tenant)
        await manager.add_user("t-1", sample_user)
        with pytest.raises(ValueError, match="already exists"):
            await manager.add_user("t-1", sample_user)

    async def test_remove_user(
        self, manager: TenantManager, sample_tenant: Tenant, sample_user: TenantUser
    ) -> None:
        await manager.create_tenant(sample_tenant)
        await manager.add_user("t-1", sample_user)
        await manager.remove_user("t-1", "u-1")
        with pytest.raises(UserNotFoundError):
            await manager.get_user("t-1", "u-1")

    async def test_remove_nonexistent_user_raises(
        self, manager: TenantManager, sample_tenant: Tenant
    ) -> None:
        await manager.create_tenant(sample_tenant)
        with pytest.raises(UserNotFoundError):
            await manager.remove_user("t-1", "u-1")

    async def test_get_user(
        self, manager: TenantManager, sample_tenant: Tenant, sample_user: TenantUser
    ) -> None:
        await manager.create_tenant(sample_tenant)
        await manager.add_user("t-1", sample_user)
        result = await manager.get_user("t-1", "u-1")
        assert result.email == "user@acme.com"

    async def test_get_user_not_found(self, manager: TenantManager, sample_tenant: Tenant) -> None:
        await manager.create_tenant(sample_tenant)
        with pytest.raises(UserNotFoundError):
            await manager.get_user("t-1", "u-1")

    async def test_list_users(self, manager: TenantManager, sample_tenant: Tenant) -> None:
        await manager.create_tenant(sample_tenant)
        u1 = TenantUser(id="u-1", tenant_id="t-1", email="a@a.com")
        u2 = TenantUser(id="u-2", tenant_id="t-1", email="b@b.com")
        await manager.add_user("t-1", u1)
        await manager.add_user("t-1", u2)
        users = await manager.list_users("t-1")
        assert len(users) == 2

    async def test_list_users_tenant_not_found(self, manager: TenantManager) -> None:
        with pytest.raises(TenantNotFoundError):
            await manager.list_users("nonexistent")

    async def test_check_quota(self, manager: TenantManager, sample_tenant: Tenant) -> None:
        await manager.create_tenant(sample_tenant)
        quota = TenantQuota(tenant_id="t-1", resource_type="agents", hard_limit=10, soft_limit=8)
        manager.set_quota("t-1", quota)
        result = await manager.check_quota("t-1", "agents")
        assert result.hard_limit == 10
        assert result.current_usage == 0

    async def test_check_quota_not_found(
        self, manager: TenantManager, sample_tenant: Tenant
    ) -> None:
        await manager.create_tenant(sample_tenant)
        with pytest.raises(ValueError, match="No quota defined"):
            await manager.check_quota("t-1", "agents")

    async def test_update_quota_usage(self, manager: TenantManager, sample_tenant: Tenant) -> None:
        await manager.create_tenant(sample_tenant)
        quota = TenantQuota(tenant_id="t-1", resource_type="agents", hard_limit=10, soft_limit=8)
        manager.set_quota("t-1", quota)
        result = await manager.update_quota_usage("t-1", "agents", 3)
        assert result.current_usage == 3
        assert result.remaining == 7

    async def test_update_quota_usage_decrement(
        self, manager: TenantManager, sample_tenant: Tenant
    ) -> None:
        await manager.create_tenant(sample_tenant)
        quota = TenantQuota(
            tenant_id="t-1",
            resource_type="agents",
            hard_limit=10,
            soft_limit=8,
            current_usage=5,
            remaining=5,
        )
        manager.set_quota("t-1", quota)
        result = await manager.update_quota_usage("t-1", "agents", -2)
        assert result.current_usage == 3
        assert result.remaining == 7

    async def test_update_quota_usage_not_found(
        self, manager: TenantManager, sample_tenant: Tenant
    ) -> None:
        await manager.create_tenant(sample_tenant)
        with pytest.raises(ValueError, match="No quota defined"):
            await manager.update_quota_usage("t-1", "agents", 1)

    async def test_update_quota_usage_suspended_tenant_raises(self, manager: TenantManager) -> None:
        tenant = Tenant(id="t-1", name="A", slug="a", status=TenantStatus.SUSPENDED)
        await manager.create_tenant(tenant)
        with pytest.raises(TenantSuspendedError, match="suspended"):
            await manager.update_quota_usage("t-1", "agents", 1)

    async def test_get_feature_status_available(
        self, manager: TenantManager, sample_tenant: Tenant
    ) -> None:
        tenant = sample_tenant.model_copy(update={"features": ("audit", "analytics")})
        await manager.create_tenant(tenant)
        assert await manager.get_feature_status("t-1", "audit") is True
        assert await manager.get_feature_status("t-1", "analytics") is True

    async def test_get_feature_status_not_available(
        self, manager: TenantManager, sample_tenant: Tenant
    ) -> None:
        tenant = sample_tenant.model_copy(update={"features": ("audit",)})
        await manager.create_tenant(tenant)
        assert await manager.get_feature_status("t-1", "analytics") is False

    async def test_get_feature_status_tenant_not_found(self, manager: TenantManager) -> None:
        with pytest.raises(TenantNotFoundError):
            await manager.get_feature_status("nonexistent", "audit")
