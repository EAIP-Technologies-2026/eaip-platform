"""Floating license manager — pool management and lease lifecycle."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any

from eaip.floatlicense.events import (
    LicenseCheckedIn,
    LicenseCheckedOut,
    LicenseExhausted,
)
from eaip.floatlicense.exceptions import PoolNotFoundError
from eaip.floatlicense.models import (
    LeaseStatus,
    LicenseConfig,
    LicenseLease,
    LicensePool,
)
from eaip.shared.time import utc_now

EventCallback = Callable[[Any], Any]


class FloatingLicenseManager:
    def __init__(
        self,
        config: LicenseConfig | None = None,
        event_callback: EventCallback | None = None,
    ) -> None:
        self._config = config or LicenseConfig()
        self._pools: dict[str, LicensePool] = {}
        self._leases: dict[str, LicenseLease] = {}
        self._event_callback = event_callback

    def set_event_callback(self, callback: EventCallback | None) -> None:
        self._event_callback = callback

    def _emit(self, event: Any) -> None:
        if self._event_callback:
            self._event_callback(event)

    # -- Pool management -----------------------------------------------------

    async def create_pool(
        self,
        name: str,
        total_licenses: int,
        vendor: str,
        product: str,
        *,
        expiration: datetime | None = None,
    ) -> LicensePool:
        pool = LicensePool(
            id=str(uuid.uuid4()),
            name=name,
            total_licenses=total_licenses,
            available_licenses=total_licenses,
            vendor=vendor,
            product=product,
            expiration=expiration,
        )
        self._pools[pool.id] = pool
        return pool

    async def get_pool(self, pool_id: str) -> LicensePool:
        if pool_id not in self._pools:
            raise PoolNotFoundError(
                f"Pool not found: {pool_id}",
                context={"pool_id": pool_id},
            )
        return self._pools[pool_id]

    async def list_pools(self) -> list[LicensePool]:
        return list(self._pools.values())

    async def update_pool_available(
        self,
        pool_id: str,
        delta: int,
    ) -> LicensePool:
        pool = await self.get_pool(pool_id)
        new_available = max(0, pool.available_licenses + delta)
        updated = LicensePool(
            id=pool.id,
            name=pool.name,
            total_licenses=pool.total_licenses,
            available_licenses=new_available,
            vendor=pool.vendor,
            product=pool.product,
            expiration=pool.expiration,
        )
        self._pools[pool_id] = updated
        return updated

    # -- Lease lifecycle -----------------------------------------------------

    async def check_out(
        self,
        pool_id: str,
        licensee: str,
    ) -> LicenseLease:
        pool = await self.get_pool(pool_id)

        active = [
            l
            for l in self._leases.values()
            if l.pool_id == pool_id and l.licensee == licensee and l.status == LeaseStatus.ACTIVE
        ]
        if len(active) >= self._config.max_leases_per_licensee:
            raise RuntimeError(f"Licensee '{licensee}' already has {len(active)} active lease(s)")

        if pool.available_licenses < 1:
            self._emit(
                LicenseExhausted(
                    pool_id=pool_id,
                    name=pool.name,
                    vendor=pool.vendor,
                    product=pool.product,
                    attempted_licensee=licensee,
                )
            )
            raise RuntimeError(f"No available licenses in pool '{pool.name}'")

        lease = LicenseLease(
            id=str(uuid.uuid4()),
            pool_id=pool_id,
            licensee=licensee,
        )
        self._leases[lease.id] = lease
        await self.update_pool_available(pool_id, -1)
        self._emit(
            LicenseCheckedOut(
                pool_id=pool_id,
                lease_id=lease.id,
                licensee=licensee,
            )
        )
        return lease

    async def check_in(
        self,
        lease_id: str,
    ) -> LicenseLease:
        if lease_id not in self._leases:
            raise RuntimeError(f"Lease not found: {lease_id}")

        lease = self._leases[lease_id]
        if lease.status != LeaseStatus.ACTIVE:
            raise RuntimeError(f"Lease {lease_id} is not active")

        now = utc_now()
        updated = LicenseLease(
            id=lease.id,
            pool_id=lease.pool_id,
            licensee=lease.licensee,
            checked_out_at=lease.checked_out_at,
            checked_in_at=now,
            status=LeaseStatus.RETURNED,
        )
        self._leases[lease_id] = updated
        await self.update_pool_available(lease.pool_id, 1)
        self._emit(
            LicenseCheckedIn(
                pool_id=lease.pool_id,
                lease_id=lease_id,
                licensee=lease.licensee,
                checked_in_at=now,
            )
        )
        return updated

    async def get_lease(self, lease_id: str) -> LicenseLease:
        if lease_id not in self._leases:
            raise RuntimeError(f"Lease not found: {lease_id}")
        return self._leases[lease_id]

    async def list_leases(
        self,
        pool_id: str | None = None,
        status: LeaseStatus | None = None,
    ) -> list[LicenseLease]:
        result = list(self._leases.values())
        if pool_id:
            result = [l for l in result if l.pool_id == pool_id]
        if status:
            result = [l for l in result if l.status == status]
        return result

    async def release_expired_leases(self) -> list[LicenseLease]:
        now = utc_now()
        released: list[LicenseLease] = []
        for lease in list(self._leases.values()):
            if lease.status != LeaseStatus.ACTIVE:
                continue
            elapsed = (now - lease.checked_out_at).total_seconds()
            if elapsed > self._config.default_lease_duration_minutes * 60:
                updated = await self.check_in(lease.id)
                released.append(updated)
        return released


__all__ = ["FloatingLicenseManager"]
