"""License enforcement — feature access, quota enforcement, and restriction checks."""

from __future__ import annotations

from typing import Any

from eaip.license.events import FeatureAccessDenied, FeatureAccessGranted
from eaip.license.manager import LicenseManager
from eaip.license.models import LicenseStatus
from eaip.shared.time import utc_now


class LicenseEnforcer:
    """Enforces license restrictions for feature access and quota limits."""

    def __init__(self, manager: LicenseManager) -> None:
        self._manager = manager

    async def check_feature_access(
        self,
        license_id: str,
        feature_key: str,
    ) -> tuple[bool, str]:
        """Check if a license is entitled to a feature.

        Returns:
            Tuple of (allowed, reason).
        """
        try:
            lic = await self._manager.get_license(license_id)
        except Exception:
            return False, "License not found"

        if lic.status != LicenseStatus.ACTIVE:
            msg = f"License status is {lic.status.value}"
            self._manager._emit(
                FeatureAccessDenied(
                    license_id=license_id,
                    feature_key=feature_key,
                    reason=msg,
                )
            )
            return False, msg

        if feature_key not in lic.features:
            msg = f"Feature '{feature_key}' is not entitled"
            self._manager._emit(
                FeatureAccessDenied(
                    license_id=license_id,
                    feature_key=feature_key,
                    reason=msg,
                )
            )
            return False, msg

        entitled = await self._manager.get_entitlement(license_id, feature_key)
        if not entitled:
            msg = f"Feature '{feature_key}' entitlement is disabled"
            self._manager._emit(
                FeatureAccessDenied(
                    license_id=license_id,
                    feature_key=feature_key,
                    reason=msg,
                )
            )
            return False, msg

        self._manager._emit(
            FeatureAccessGranted(
                license_id=license_id,
                feature_key=feature_key,
            )
        )
        return True, "Access granted"

    async def check_quota_enforcement(
        self,
        license_id: str,
        resource_type: str,
    ) -> tuple[bool, int, int]:
        """Check the current quota usage for a resource type.

        Returns:
            Tuple of (allowed, current_usage, max_quota).
        """
        lic = await self._manager.get_license(license_id)
        max_val = self._manager._quota_max(lic, resource_type)
        current = self._manager._count_usage(license_id, resource_type)
        allowed = lic.status == LicenseStatus.ACTIVE and current < max_val
        return allowed, current, max_val

    async def get_restrictions(self, license_id: str) -> dict[str, Any]:
        """Get all restrictions for a license.

        Returns:
            Dictionary of restriction details.
        """
        lic = await self._manager.get_license(license_id)
        now = utc_now()

        restrictions: dict[str, Any] = {
            "is_active": lic.status == LicenseStatus.ACTIVE,
            "status": lic.status.value,
            "features": list(lic.features),
            "max_users": lic.max_users,
            "max_agents": lic.max_agents,
            "max_workflows": lic.max_workflows,
            "max_storage_bytes": lic.max_storage_bytes,
        }

        if lic.expires_at:
            restrictions["expires_at"] = lic.expires_at.isoformat()
            restrictions["is_expired"] = now > lic.expires_at
        else:
            restrictions["is_expired"] = False

        return restrictions

    async def is_license_active(self, license_id: str) -> bool:
        """Check if a license is in active status."""
        try:
            lic = await self._manager.get_license(license_id)
            return lic.status == LicenseStatus.ACTIVE
        except Exception:
            return False


__all__ = ["LicenseEnforcer"]
