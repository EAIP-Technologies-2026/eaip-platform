"""Runtime module integration for the pipeline orchestration subsystem."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.porch.health import PorchHealthCheck

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class PorchRuntimeModule:
    name: str = "porch"

    def __init__(self) -> None:
        self._health_check = PorchHealthCheck()
        self._log = get_logger("eaip.porch.integration")

    @property
    def health_check(self) -> PorchHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("porch.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("porch.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("porch.module.stopping")


__all__ = ["PorchRuntimeModule"]
