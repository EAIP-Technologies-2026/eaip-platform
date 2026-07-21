"""Platform health runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.phealth.health import PlatformHealthHealthCheck

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class PlatformHealthRuntimeModule:
    """Runtime module for platform health monitoring."""

    name: str = "phealth"

    def __init__(self) -> None:
        """Initialize the platform health runtime module."""
        self._health_check = PlatformHealthHealthCheck()
        self._log = get_logger("eaip.phealth.integration")

    @property
    def health_check(self) -> PlatformHealthHealthCheck:
        """Return the platform health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("phealth.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("phealth.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("phealth.module.stopping")


__all__ = ["PlatformHealthRuntimeModule"]
