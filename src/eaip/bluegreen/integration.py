"""Blue-green deployment runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.bluegreen.health import BlueGreenHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class BlueGreenRuntimeModule:
    """Runtime module for the blue-green deployment manager."""

    name: str = "bluegreen"

    def __init__(self) -> None:
        """Initialize the blue-green runtime module."""
        self._health_check = BlueGreenHealthCheck()
        self._log = get_logger("eaip.bluegreen.integration")

    @property
    def health_check(self) -> BlueGreenHealthCheck:
        """Return the blue-green health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("bluegreen.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("bluegreen.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("bluegreen.module.stopping")


__all__ = ["BlueGreenRuntimeModule"]
