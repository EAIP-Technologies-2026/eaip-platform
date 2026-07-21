"""Runtime module integration for the metering subsystem."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.metering.health import MeteringHealthCheck

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class MeteringRuntimeModule:
    name: str = "metering"

    def __init__(self) -> None:
        self._health_check = MeteringHealthCheck()
        self._log = get_logger("eaip.metering.integration")

    @property
    def health_check(self) -> MeteringHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("metering.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("metering.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("metering.module.stopping")


__all__ = ["MeteringRuntimeModule"]
