"""Incident communication runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.inccomm.health import IncidentCommHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class IncidentCommRuntimeModule:
    """Runtime module for incident communication."""

    name: str = "inccomm"

    def __init__(self) -> None:
        """Initialize the runtime module."""
        self._health_check = IncidentCommHealthCheck()
        self._log = get_logger("eaip.inccomm.integration")

    @property
    def health_check(self) -> IncidentCommHealthCheck:
        """Return the health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("inccomm.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("inccomm.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("inccomm.module.stopping")


__all__ = ["IncidentCommRuntimeModule"]
