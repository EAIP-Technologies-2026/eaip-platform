"""Health check for the configuration management module."""

from __future__ import annotations

from eaip.configmgt.manager import ConfigManager
from eaip.health.checks import HealthReport, HealthStatus


class ConfigMgtHealthCheck:
    name: str = "configmgt"

    def __init__(self, manager: ConfigManager) -> None:
        self._manager = manager

    async def check(self) -> HealthReport:
        entries = await self._manager.list_entries()
        profiles = await self._manager.list_profiles()
        changes = await self._manager.list_changes()

        details = {
            "entries_total": len(entries),
            "profiles_total": len(profiles),
            "changes_total": len(changes),
            "snapshots_total": len(self._manager._snapshots),
            "hot_reload_enabled": self._manager._config.enable_hot_reload,
            "audit_logging_enabled": self._manager._config.enable_audit_logging,
            "versioning_enabled": self._manager._config.enable_versioning,
        }

        status = HealthStatus.HEALTHY
        messages: list[str] = []

        if not entries:
            messages.append("No config entries registered")
            status = HealthStatus.DEGRADED

        if not profiles:
            messages.append("No config profiles configured")

        return HealthReport(
            component="configmgt",
            status=status,
            message="; ".join(messages) if messages else "Configuration management is operational",
            details=details,
        )


__all__ = ["ConfigMgtHealthCheck"]
