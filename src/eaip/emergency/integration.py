"""Emergency access manager runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.emergency.health import EmergencyHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class EmergencyRuntimeModule:
    """Runtime module for the emergency access manager."""

    name: str = "emergency"

    def __init__(self) -> None:
        """Initialize the emergency runtime module."""
        self._health_check = EmergencyHealthCheck()
        self._log = get_logger("eaip.emergency.integration")

    @property
    def health_check(self) -> EmergencyHealthCheck:
        """Return the emergency health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("emergency.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("emergency.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("emergency.module.stopping")


__all__ = ["EmergencyRuntimeModule"]
