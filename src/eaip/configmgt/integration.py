"""Runtime module integration for the configuration management module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.configmgt.health import ConfigMgtHealthCheck
from eaip.configmgt.manager import ConfigManager
from eaip.configmgt.models import ConfigMgtConfig
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ConfigMgtRuntimeModule:
    name: str = "configmgt"

    def __init__(
        self,
        config: ConfigMgtConfig | None = None,
        manager: ConfigManager | None = None,
    ) -> None:
        self._config = config or ConfigMgtConfig()
        self._manager = manager or ConfigManager(config=self._config)
        self._log = get_logger("eaip.configmgt.integration")

    @property
    def manager(self) -> ConfigManager:
        return self._manager

    @property
    def config(self) -> ConfigMgtConfig:
        return self._config

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("configmgt.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.configmgt",
            title="Configuration Management",
            description="Distributed configuration management with hot reload, config validation, secrets integration, and version tracking",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("configmgt", "configuration", "hot-reload", "validation", "versioning"),
        )
        platform.capabilities.register(capability)
        platform.health.register(ConfigMgtHealthCheck(manager=self._manager))
        self._log.info("configmgt.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        self._log.info("configmgt.module.stopping")


__all__ = ["ConfigMgtRuntimeModule"]
