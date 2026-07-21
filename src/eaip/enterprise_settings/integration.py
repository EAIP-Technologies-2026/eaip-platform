"""Runtime module integration for the enterprise settings module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.enterprise_settings.health import EnterpriseSettingsHealthCheck
from eaip.enterprise_settings.models import SettingsConfig
from eaip.enterprise_settings.service import EnterpriseSettingsService
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class EnterpriseSettingsRuntimeModule:
    """Runtime module integration for enterprise settings."""

    name: str = "enterprise_settings"

    def __init__(
        self,
        config: SettingsConfig | None = None,
        service: EnterpriseSettingsService | None = None,
    ) -> None:
        """Initialize the runtime module."""
        self._config = config or SettingsConfig()
        self._service = service or EnterpriseSettingsService(config=self._config)
        self._log = get_logger("eaip.enterprise_settings.integration")

    @property
    def service(self) -> EnterpriseSettingsService:
        """Return the underlying enterprise settings service."""
        return self._service

    @property
    def config(self) -> SettingsConfig:
        """Return the module configuration."""
        return self._config

    async def start(self, kernel: RuntimeKernel) -> None:
        """Start the enterprise settings module."""
        self._log.info("enterprise_settings.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.enterprise_settings",
            title="Enterprise Settings",
            description=(
                "Enterprise-wide settings management with categories, groups, "
                "definitions, profiles, validation, audit, and export/import"
            ),
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("enterprise_settings", "settings", "configuration", "audit", "profiles"),
        )
        platform.capabilities.register(capability)
        platform.health.register(EnterpriseSettingsHealthCheck(service=self._service))
        self._log.info("enterprise_settings.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Stop the enterprise settings module."""
        self._log.info("enterprise_settings.module.stopping")


__all__ = ["EnterpriseSettingsRuntimeModule"]
