"""Health check for license & entitlement management."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus
from eaip.license.manager import LicenseManager
from eaip.license.models import LicenseStatus


class LicenseHealthCheck:
    """Health check for license management services.

    Implements the :class:`eaip.health.checks.HealthCheck` protocol.
    """

    name: str = "license"

    def __init__(self, manager: LicenseManager) -> None:
        self._manager = manager

    async def check(self) -> HealthReport:
        details: dict[str, object] = {}
        try:
            all_licenses = await self._manager.list_licenses()
            details["license_count"] = len(all_licenses)
        except Exception as exc:
            return HealthReport(
                component=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"License manager unavailable: {exc}",
                details={"error": str(exc)},
            )

        active = sum(1 for l in all_licenses if l.status == LicenseStatus.ACTIVE)
        expired = sum(1 for l in all_licenses if l.status == LicenseStatus.EXPIRED)
        revoked = sum(1 for l in all_licenses if l.status == LicenseStatus.REVOKED)
        suspended = sum(1 for l in all_licenses if l.status == LicenseStatus.SUSPENDED)
        details["active_count"] = active
        details["expired_count"] = expired
        details["revoked_count"] = revoked
        details["suspended_count"] = suspended

        status = HealthStatus.HEALTHY
        messages: list[str] = []

        if revoked > 0:
            messages.append(f"{revoked} revoked license(s)")

        if active == 0 and len(all_licenses) > 0:
            status = HealthStatus.DEGRADED
            messages.append("No active licenses")

        return HealthReport(
            component=self.name,
            status=status,
            message="; ".join(messages) if messages else "License management healthy",
            details=details,
        )


__all__ = ["LicenseHealthCheck"]
