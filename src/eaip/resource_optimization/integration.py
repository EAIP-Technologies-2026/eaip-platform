"""Resource optimization runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.resource_optimization.health import ResourceOptimizationHealthCheck

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ResourceOptimizationRuntimeModule:
    """Runtime module for the resource optimization service."""

    name: str = "resource_optimization"

    def __init__(self) -> None:
        """Initialize the resource optimization runtime module."""
        self._health_check = ResourceOptimizationHealthCheck()
        self._log = get_logger("eaip.resource_optimization.integration")

    @property
    def health_check(self) -> ResourceOptimizationHealthCheck:
        """Return the resource optimization health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("resource_optimization.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("resource_optimization.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("resource_optimization.module.stopping")


__all__ = ["ResourceOptimizationRuntimeModule"]
