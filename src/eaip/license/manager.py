"""License manager — create, get, update, validate, and track license usage."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any

from eaip.license.events import (
    LicenseCreated,
    LicenseExpired,
    LicenseRevoked,
    LicenseSuspended,
    LicenseValidated,
    QuotaExceeded,
    QuotaWarning,
    UsageRecorded,
)
from eaip.license.exceptions import (
    LicenseExpiredError,
    LicenseNotFoundError,
    QuotaExceededError,
)
from eaip.license.models import (
    FeatureEntitlement,
    License,
    LicenseConfig,
    LicenseStatus,
    LicenseType,
    LicenseValidationResult,
    UsageRecord,
)
from eaip.shared.time import utc_now

EventCallback = Callable[[Any], Any]


class LicenseManager:
    """Manages license lifecycle, validation, entitlements, and usage tracking."""

    def __init__(
        self,
        config: LicenseConfig | None = None,
        event_callback: EventCallback | None = None,
    ) -> None:
        self._config = config or LicenseConfig()
        self._licenses: dict[str, License] = {}
        self._entitlements: dict[str, FeatureEntitlement] = {}
        self._usage_records: list[UsageRecord] = []
        self._event_callback = event_callback

    def set_event_callback(self, callback: EventCallback | None) -> None:
        self._event_callback = callback

    def _emit(self, event: Any) -> None:
        if self._event_callback:
            self._event_callback(event)

    # -- License CRUD -------------------------------------------------------

    async def create_license(
        self,
        name: str,
        key: str,
        *,
        license_type: LicenseType = LicenseType.TRIAL,
        features: tuple[str, ...] = (),
        max_users: int = 0,
        max_agents: int = 0,
        max_workflows: int = 0,
        max_storage_bytes: int = 0,
        expires_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
        customer_info: dict[str, Any] | None = None,
    ) -> License:
        now = utc_now()
        license_id = str(uuid.uuid4())
        lic = License(
            id=license_id,
            name=name,
            key=key,
            type=license_type,
            status=LicenseStatus.ACTIVE,
            features=features,
            max_users=max_users,
            max_agents=max_agents,
            max_workflows=max_workflows,
            max_storage_bytes=max_storage_bytes,
            issued_at=now,
            expires_at=expires_at,
            metadata=metadata or {},
            customer_info=customer_info or {},
        )
        self._licenses[license_id] = lic
        self._emit(
            LicenseCreated(
                license_id=license_id,
                name=name,
                key=key,
                license_type=license_type.value,
                features=features,
            )
        )
        return lic

    async def get_license(self, license_id: str) -> License:
        if license_id not in self._licenses:
            raise LicenseNotFoundError(
                f"License not found: {license_id}",
                context={"license_id": license_id},
            )
        return self._licenses[license_id]

    async def update_license(
        self,
        license_id: str,
        *,
        name: str | None = None,
        features: tuple[str, ...] | None = None,
        max_users: int | None = None,
        max_agents: int | None = None,
        max_workflows: int | None = None,
        max_storage_bytes: int | None = None,
        expires_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
        customer_info: dict[str, Any] | None = None,
    ) -> License:
        lic = await self.get_license(license_id)
        updated = License(
            id=lic.id,
            name=name or lic.name,
            key=lic.key,
            type=lic.type,
            status=lic.status,
            features=features if features is not None else lic.features,
            max_users=max_users if max_users is not None else lic.max_users,
            max_agents=max_agents if max_agents is not None else lic.max_agents,
            max_workflows=max_workflows if max_workflows is not None else lic.max_workflows,
            max_storage_bytes=max_storage_bytes
            if max_storage_bytes is not None
            else lic.max_storage_bytes,
            issued_at=lic.issued_at,
            expires_at=expires_at if expires_at is not None else lic.expires_at,
            last_validated_at=lic.last_validated_at,
            metadata=metadata if metadata is not None else lic.metadata,
            customer_info=customer_info if customer_info is not None else lic.customer_info,
        )
        self._licenses[license_id] = updated
        return updated

    async def revoke_license(self, license_id: str, reason: str = "") -> License:
        lic = await self.get_license(license_id)
        updated = License(
            id=lic.id,
            name=lic.name,
            key=lic.key,
            type=lic.type,
            status=LicenseStatus.REVOKED,
            features=lic.features,
            max_users=lic.max_users,
            max_agents=lic.max_agents,
            max_workflows=lic.max_workflows,
            max_storage_bytes=lic.max_storage_bytes,
            issued_at=lic.issued_at,
            expires_at=lic.expires_at,
            last_validated_at=lic.last_validated_at,
            metadata=lic.metadata,
            customer_info=lic.customer_info,
        )
        self._licenses[license_id] = updated
        self._emit(LicenseRevoked(license_id=license_id, key=lic.key, reason=reason))
        return updated

    async def suspend_license(self, license_id: str, reason: str = "") -> License:
        lic = await self.get_license(license_id)
        updated = License(
            id=lic.id,
            name=lic.name,
            key=lic.key,
            type=lic.type,
            status=LicenseStatus.SUSPENDED,
            features=lic.features,
            max_users=lic.max_users,
            max_agents=lic.max_agents,
            max_workflows=lic.max_workflows,
            max_storage_bytes=lic.max_storage_bytes,
            issued_at=lic.issued_at,
            expires_at=lic.expires_at,
            last_validated_at=lic.last_validated_at,
            metadata=lic.metadata,
            customer_info=lic.customer_info,
        )
        self._licenses[license_id] = updated
        self._emit(LicenseSuspended(license_id=license_id, key=lic.key, reason=reason))
        return updated

    async def list_licenses(
        self,
        status: LicenseStatus | None = None,
    ) -> list[License]:
        all_licenses = list(self._licenses.values())
        if status:
            all_licenses = [l for l in all_licenses if l.status == status]
        return all_licenses

    # -- Validation ---------------------------------------------------------

    async def validate_license(self, key: str) -> LicenseValidationResult:
        license_id: str | None = None
        for lid, lic in self._licenses.items():
            if lic.key == key:
                license_id = lid
                break

        if license_id is None:
            result = LicenseValidationResult(
                id=str(uuid.uuid4()),
                license_id="",
                valid=False,
                errors=("License not found",),
            )
            self._emit(
                LicenseValidated(
                    license_id="",
                    key=key,
                    valid=False,
                    errors=("License not found",),
                )
            )
            return result

        lic = self._licenses[license_id]
        errors: list[str] = []
        warnings: list[str] = []
        effective_status = lic.status

        if lic.status == LicenseStatus.REVOKED:
            errors.append("License has been revoked")
        elif lic.status == LicenseStatus.SUSPENDED:
            errors.append("License has been suspended")
        elif lic.status == LicenseStatus.ACTIVE and lic.expires_at:
            now = utc_now()
            if now > lic.expires_at:
                errors.append("License has expired")
                effective_status = LicenseStatus.EXPIRED
                self._emit(
                    LicenseExpired(
                        license_id=license_id,
                        key=key,
                        expired_at=lic.expires_at.isoformat(),
                    )
                )

        expires_in_days: int | None = None
        if lic.expires_at:
            delta = (lic.expires_at - utc_now()).days
            expires_in_days = max(delta, 0)
            if 0 < expires_in_days <= self._config.grace_period_days:
                warnings.append(f"License expires in {expires_in_days} day(s)")

        features_available: list[str] = []
        features_blocked: list[str] = []
        if effective_status == LicenseStatus.ACTIVE:
            features_available = list(lic.features)
        else:
            features_blocked = list(lic.features)

        valid = len(errors) == 0

        now = utc_now()
        updated = License(
            id=lic.id,
            name=lic.name,
            key=lic.key,
            type=lic.type,
            status=effective_status,
            features=lic.features,
            max_users=lic.max_users,
            max_agents=lic.max_agents,
            max_workflows=lic.max_workflows,
            max_storage_bytes=lic.max_storage_bytes,
            issued_at=lic.issued_at,
            expires_at=lic.expires_at,
            last_validated_at=now,
            metadata=lic.metadata,
            customer_info=lic.customer_info,
        )
        self._licenses[license_id] = updated

        result = LicenseValidationResult(
            id=str(uuid.uuid4()),
            license_id=license_id,
            valid=valid,
            errors=tuple(errors),
            warnings=tuple(warnings),
            features_available=tuple(features_available),
            features_blocked=tuple(features_blocked),
            expires_in_days=expires_in_days,
        )
        self._emit(
            LicenseValidated(
                license_id=license_id,
                key=key,
                valid=valid,
                errors=tuple(errors),
                warnings=tuple(warnings),
            )
        )
        return result

    # -- Entitlements -------------------------------------------------------

    async def get_entitlement(self, license_id: str, feature_key: str) -> bool:
        lic = await self.get_license(license_id)

        if lic.status != LicenseStatus.ACTIVE:
            return False

        if feature_key not in lic.features:
            return False

        for ent in self._entitlements.values():
            if ent.license_id == license_id and ent.feature_key == feature_key:
                return ent.enabled

        return True

    async def list_features(self, license_id: str) -> tuple[str, ...]:
        lic = await self.get_license(license_id)
        return lic.features

    # -- Quota ---------------------------------------------------------------

    async def check_quota(
        self,
        license_id: str,
        resource_type: str,
        requested: int,
    ) -> bool:
        lic = await self.get_license(license_id)

        if lic.status != LicenseStatus.ACTIVE:
            return False

        current = self._count_usage(license_id, resource_type)
        max_val = self._quota_max(lic, resource_type)
        allowed = (current + requested) <= max_val

        if allowed and max_val > 0:
            usage_pct = ((current + requested) / max_val) * 100
            if usage_pct >= 80:
                self._emit(
                    QuotaWarning(
                        license_id=license_id,
                        resource_type=resource_type,
                        current=current + requested,
                        max=max_val,
                        usage_percent=usage_pct,
                    )
                )

        if not allowed:
            self._emit(
                QuotaExceeded(
                    license_id=license_id,
                    resource_type=resource_type,
                    current=current,
                    max=max_val,
                    requested=requested,
                )
            )
            raise QuotaExceededError(
                f"{resource_type} quota exceeded: {current + requested} > {max_val}",
                context={
                    "license_id": license_id,
                    "resource_type": resource_type,
                    "current": current,
                    "max": max_val,
                    "requested": requested,
                },
            )

        return True

    def _count_usage(self, license_id: str, resource_type: str) -> int:
        if resource_type == "users":
            return 0
        if resource_type == "agents":
            return 0
        if resource_type == "workflows":
            return 0
        if resource_type == "storage_bytes":
            return 0
        total = 0
        for rec in self._usage_records:
            if rec.license_id == license_id and rec.metric == resource_type:
                total += rec.quantity
        return total

    def _quota_max(self, lic: License, resource_type: str) -> int:
        mapping = {
            "users": lic.max_users,
            "agents": lic.max_agents,
            "workflows": lic.max_workflows,
            "storage_bytes": lic.max_storage_bytes,
        }
        return mapping.get(resource_type, 0)

    # -- Usage tracking -----------------------------------------------------

    async def record_usage(
        self,
        license_id: str,
        feature: str,
        metric: str,
        quantity: int = 1,
        metadata: dict[str, Any] | None = None,
    ) -> UsageRecord:
        lic = await self.get_license(license_id)
        if lic.status != LicenseStatus.ACTIVE:
            raise LicenseExpiredError(
                f"Cannot record usage for non-active license: {license_id}",
                context={"license_id": license_id, "status": lic.status.value},
            )

        if not self._config.enable_usage_tracking:
            raise RuntimeError("Usage tracking is disabled")

        rec = UsageRecord(
            id=str(uuid.uuid4()),
            license_id=license_id,
            feature_key=feature,
            metric=metric,
            quantity=quantity,
            metadata=metadata or {},
        )
        self._usage_records.append(rec)
        self._emit(
            UsageRecorded(
                license_id=license_id,
                feature_key=feature,
                metric=metric,
                quantity=quantity,
                metadata=metadata or {},
            )
        )
        return rec

    # -- Entitlement CRUD ----------------------------------------------------

    async def create_entitlement(
        self,
        license_id: str,
        feature_key: str,
        enabled: bool = True,
        limits: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> FeatureEntitlement:
        ent = FeatureEntitlement(
            id=str(uuid.uuid4()),
            license_id=license_id,
            feature_key=feature_key,
            enabled=enabled,
            limits=limits or {},
            metadata=metadata or {},
        )
        self._entitlements[ent.id] = ent
        return ent

    async def get_entitlements(self, license_id: str) -> list[FeatureEntitlement]:
        return [e for e in self._entitlements.values() if e.license_id == license_id]

    async def get_usage_records(
        self,
        license_id: str,
        limit: int = 100,
    ) -> list[UsageRecord]:
        records = [r for r in self._usage_records if r.license_id == license_id]
        return sorted(records, key=lambda r: r.timestamp, reverse=True)[:limit]


__all__ = ["LicenseManager"]
