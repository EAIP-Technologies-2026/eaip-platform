"""Tenant manager — tenant lifecycle, user management, and quota enforcement."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from eaip.logging.context import get_logger
from eaip.tenants.events import (
    QuotaExceeded,
    QuotaWarning,
    TenantActivated,
    TenantClosed,
    TenantCreated,
    TenantSuspended,
    TenantUpdated,
    UserAdded,
    UserRemoved,
)
from eaip.tenants.exceptions import (
    TenantNotFoundError,
    TenantSuspendedError,
    UserNotFoundError,
)
from eaip.tenants.models import (
    Tenant,
    TenantQuota,
    TenantStatus,
    TenantUser,
)

if TYPE_CHECKING:
    from eaip.events.bus import EventBus


class TenantManager:
    """Manages tenant lifecycle, users, and quota enforcement."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._event_bus = event_bus
        self._log = get_logger("eaip.tenants.manager")
        self._tenants: dict[str, Tenant] = {}
        self._users: dict[str, dict[str, TenantUser]] = {}
        self._quotas: dict[str, dict[str, TenantQuota]] = {}
        self._features: dict[str, set[str]] = {}

    async def create_tenant(self, tenant: Tenant) -> Tenant:
        if tenant.id in self._tenants:
            raise ValueError(f"Tenant {tenant.id!r} already exists")
        self._tenants[tenant.id] = tenant
        self._users[tenant.id] = {}
        self._quotas[tenant.id] = {}
        self._features[tenant.id] = set(tenant.features)
        if self._event_bus is not None:
            await self._event_bus.publish(
                TenantCreated(
                    tenant_id=tenant.id,
                    name=tenant.name,
                    slug=tenant.slug,
                    plan=tenant.plan.value,
                )
            )
        self._log.info("tenant.created", tenant_id=tenant.id, slug=tenant.slug)
        return tenant

    async def get_tenant(self, tenant_id: str) -> Tenant:
        tenant = self._tenants.get(tenant_id)
        if tenant is None:
            raise TenantNotFoundError(f"Tenant {tenant_id!r} not found")
        return tenant

    async def update_tenant(self, tenant_id: str, updates: dict[str, Any]) -> Tenant:
        tenant = await self.get_tenant(tenant_id)
        updated = tenant.model_copy(update=updates, deep=True)
        self._tenants[tenant_id] = updated
        if self._event_bus is not None:
            await self._event_bus.publish(TenantUpdated(tenant_id=tenant_id, changes=updates))
        self._log.info("tenant.updated", tenant_id=tenant_id)
        return updated

    async def suspend_tenant(self, tenant_id: str) -> Tenant:
        tenant = await self.get_tenant(tenant_id)
        if tenant.status is TenantStatus.CLOSED:
            raise TenantSuspendedError("Cannot suspend a closed tenant")
        updated = tenant.model_copy(update={"status": TenantStatus.SUSPENDED}, deep=True)
        self._tenants[tenant_id] = updated
        if self._event_bus is not None:
            await self._event_bus.publish(
                TenantSuspended(tenant_id=tenant_id, reason="suspended_by_operator")
            )
        self._log.info("tenant.suspended", tenant_id=tenant_id)
        return updated

    async def activate_tenant(self, tenant_id: str) -> Tenant:
        tenant = await self.get_tenant(tenant_id)
        if tenant.status is TenantStatus.CLOSED:
            raise TenantSuspendedError("Cannot activate a closed tenant")
        updated = tenant.model_copy(update={"status": TenantStatus.ACTIVE}, deep=True)
        self._tenants[tenant_id] = updated
        if self._event_bus is not None:
            await self._event_bus.publish(TenantActivated(tenant_id=tenant_id))
        self._log.info("tenant.activated", tenant_id=tenant_id)
        return updated

    async def close_tenant(self, tenant_id: str) -> Tenant:
        tenant = await self.get_tenant(tenant_id)
        updated = tenant.model_copy(update={"status": TenantStatus.CLOSED}, deep=True)
        self._tenants[tenant_id] = updated
        if self._event_bus is not None:
            await self._event_bus.publish(
                TenantClosed(tenant_id=tenant_id, reason="closed_by_operator")
            )
        self._log.info("tenant.closed", tenant_id=tenant_id)
        return updated

    async def list_tenants(
        self, status: TenantStatus | None = None, plan: str | None = None
    ) -> list[Tenant]:
        results = list(self._tenants.values())
        if status is not None:
            results = [t for t in results if t.status is status]
        if plan is not None:
            results = [t for t in results if t.plan.value == plan]
        return results

    async def add_user(self, tenant_id: str, user: TenantUser) -> TenantUser:
        self._require_active(tenant_id)
        if tenant_id not in self._users:
            raise TenantNotFoundError(f"Tenant {tenant_id!r} not found")
        if user.id in self._users[tenant_id]:
            raise ValueError(f"User {user.id!r} already exists in tenant")
        self._users[tenant_id][user.id] = user
        if self._event_bus is not None:
            await self._event_bus.publish(
                UserAdded(tenant_id=tenant_id, user_id=user.id, email=user.email)
            )
        self._log.info("tenant.user_added", tenant_id=tenant_id, user_id=user.id)
        return user

    async def remove_user(self, tenant_id: str, user_id: str) -> None:
        if tenant_id not in self._users or user_id not in self._users[tenant_id]:
            raise UserNotFoundError(f"User {user_id!r} not found in tenant {tenant_id!r}")
        del self._users[tenant_id][user_id]
        if self._event_bus is not None:
            await self._event_bus.publish(UserRemoved(tenant_id=tenant_id, user_id=user_id))
        self._log.info("tenant.user_removed", tenant_id=tenant_id, user_id=user_id)

    async def get_user(self, tenant_id: str, user_id: str) -> TenantUser:
        if tenant_id not in self._users or user_id not in self._users[tenant_id]:
            raise UserNotFoundError(f"User {user_id!r} not found in tenant {tenant_id!r}")
        return self._users[tenant_id][user_id]

    async def list_users(self, tenant_id: str) -> list[TenantUser]:
        if tenant_id not in self._users:
            raise TenantNotFoundError(f"Tenant {tenant_id!r} not found")
        return list(self._users[tenant_id].values())

    async def check_quota(self, tenant_id: str, resource_type: str) -> TenantQuota:
        quotas = self._quotas.get(tenant_id, {})
        quota = quotas.get(resource_type)
        if quota is None:
            raise ValueError(f"No quota defined for {resource_type!r} on tenant {tenant_id!r}")
        return quota

    async def update_quota_usage(
        self, tenant_id: str, resource_type: str, delta: int
    ) -> TenantQuota:
        self._require_active(tenant_id)
        quotas = self._quotas.get(tenant_id, {})
        quota = quotas.get(resource_type)
        if quota is None:
            raise ValueError(f"No quota defined for {resource_type!r} on tenant {tenant_id!r}")
        new_usage = max(0, quota.current_usage + delta)
        new_remaining = quota.hard_limit - new_usage
        updated = quota.model_copy(
            update={
                "current_usage": new_usage,
                "remaining": new_remaining,
            }
        )
        quotas[resource_type] = updated
        if new_remaining <= 0 and self._event_bus is not None:
            await self._event_bus.publish(
                QuotaExceeded(
                    tenant_id=tenant_id,
                    resource_type=resource_type,
                    hard_limit=quota.hard_limit,
                    current_usage=new_usage,
                )
            )
        if new_usage >= quota.soft_limit and new_remaining > 0 and self._event_bus is not None:
            await self._event_bus.publish(
                QuotaWarning(
                    tenant_id=tenant_id,
                    resource_type=resource_type,
                    soft_limit=quota.soft_limit,
                    current_usage=new_usage,
                )
            )
        return updated

    def set_quota(self, tenant_id: str, quota: TenantQuota) -> None:
        if tenant_id not in self._quotas:
            self._quotas[tenant_id] = {}
        self._quotas[tenant_id][quota.resource_type] = quota

    async def get_feature_status(self, tenant_id: str, feature: str) -> bool:
        await self.get_tenant(tenant_id)
        tenant_features = self._features.get(tenant_id, set())
        return feature in tenant_features

    def _require_active(self, tenant_id: str) -> None:
        tenant = self._tenants.get(tenant_id)
        if tenant is None:
            raise TenantNotFoundError(f"Tenant {tenant_id!r} not found")
        if tenant.status is TenantStatus.SUSPENDED:
            raise TenantSuspendedError(f"Tenant {tenant_id!r} is suspended")
        if tenant.status is TenantStatus.CLOSED:
            raise TenantSuspendedError(f"Tenant {tenant_id!r} is closed")
