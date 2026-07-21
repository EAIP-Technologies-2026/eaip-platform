"""Health check for the enterprise settings module."""

from __future__ import annotations

from eaip.enterprise_settings.service import EnterpriseSettingsService
from eaip.health.checks import HealthReport, HealthStatus


class EnterpriseSettingsHealthCheck:
    """Health check for the enterprise settings module."""

    name: str = "enterprise_settings"

    def __init__(self, service: EnterpriseSettingsService) -> None:
        """Initialize with the enterprise settings service."""
        self._service = service

    async def check(self) -> HealthReport:
        """Run a health check against the enterprise settings service."""
        settings = await self._service.list_settings()
        categories = await self._service.list_categories()
        profiles = await self._service.list_profiles()

        details = {
            "settings_total": len(settings),
            "categories_total": len(categories),
            "profiles_total": len(profiles),
            "audit_enabled": self._service._config.enable_audit,
            "validation_enabled": self._service._config.enable_validation,
            "versioning_enabled": self._service._config.enable_versioning,
        }

        status = HealthStatus.HEALTHY
        messages: list[str] = []

        if not settings:
            messages.append("No enterprise settings registered")
            status = HealthStatus.DEGRADED

        if not profiles:
            messages.append("No settings profiles configured")

        return HealthReport(
            component="enterprise_settings",
            status=status,
            message="; ".join(messages) if messages else "Enterprise settings are operational",
            details=details,
        )


__all__ = ["EnterpriseSettingsHealthCheck"]
