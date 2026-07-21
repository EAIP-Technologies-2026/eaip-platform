"""Model monitor runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.modelmon.health import ModelMonitorHealthCheck

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ModelMonitorRuntimeModule:
    """Runtime module for the model monitor."""

    name: str = "modelmon"

    def __init__(self) -> None:
        """Initialize the model monitor runtime module."""
        self._health_check = ModelMonitorHealthCheck()
        self._log = get_logger("eaip.modelmon.integration")

    @property
    def health_check(self) -> ModelMonitorHealthCheck:
        """Return the model monitor health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("modelmon.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("modelmon.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("modelmon.module.stopping")


__all__ = ["ModelMonitorRuntimeModule"]
