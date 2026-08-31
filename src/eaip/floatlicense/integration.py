"""Floating license management runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.floatlicense.health import FloatLicenseHealthCheck
from eaip.floatlicense.manager import FloatingLicenseManager
from eaip.floatlicense.models import LicenseConfig
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class FloatLicenseRuntimeModule:
    name: str = "floatlicense"

    def __init__(
        self,
        config: LicenseConfig | None = None,
        manager: FloatingLicenseManager | None = None,
    ) -> None:
        self._config = config or LicenseConfig()
        self._manager = manager or FloatingLicenseManager(config=self._config)
        self._health_check = FloatLicenseHealthCheck(self._manager)
        self._log = get_logger("eaip.floatlicense.integration")

    @property
    def config(self) -> LicenseConfig:
        return self._config

    @property
    def manager(self) -> FloatingLicenseManager:
        return self._manager

    @property
    def health_check(self) -> FloatLicenseHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("floatlicense.module.starting")
        platform = kernel.platform

        capability = Capability(
            name="eaip.floatlicense",
            title="Floating License Manager",
            description=(
                "License pool allocation, lease management, "
                "and vendor-granted floating license tracking"
            ),
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("license", "float", "floating", "lease"),
        )
        platform.capabilities.register(capability)
        platform.health.register(self._health_check)
        kernel.register_module("floatlicense.manager", self._manager)
        self._log.info("floatlicense.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        self._log.info("floatlicense.module.stopping")


__all__ = ["FloatLicenseRuntimeModule"]
