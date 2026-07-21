"""RuntimeKernel integration — registers ScaffoldService as a RuntimeModule."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from eaip.bootstrap.health import BootstrapHealthCheck
from eaip.bootstrap.scaffold import ScaffoldService
from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class BootstrapRuntimeModule:
    name: str = "bootstrap"

    def __init__(
        self,
        scaffold_service: ScaffoldService | None = None,
        event_bus: Any = None,
    ) -> None:
        self._event_bus = event_bus
        self._scaffold = scaffold_service or ScaffoldService(event_bus=event_bus)
        self._health_check = BootstrapHealthCheck()
        self._log = get_logger("eaip.bootstrap.integration")

    @property
    def scaffold(self) -> ScaffoldService:
        return self._scaffold

    async def start(self, kernel: RuntimeKernel) -> None:
        t0 = time.monotonic()
        self._log.info("bootstrap.module.start")

        kernel.platform.health.register(self._health_check)
        kernel.platform.capabilities.register(
            Capability(
                name="bootstrap:scaffold",
                title="Platform Bootstrap & Init",
                status=CapabilityStatus.ENABLED,
                tags=("bootstrap", "scaffold", "init"),
            )
        )

        kernel.register_module("bootstrap.scaffold", self._scaffold)

        self._log.info(
            "bootstrap.module.complete",
            duration_s=round(time.monotonic() - t0, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("bootstrap.module.stop")


__all__ = ["BootstrapRuntimeModule"]
