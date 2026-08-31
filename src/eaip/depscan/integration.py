"""Dependency scanner runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.depscan.health import DependencyScannerHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class DependencyScannerRuntimeModule:
    """Runtime module for dependency scanning."""

    name: str = "depscan"

    def __init__(self) -> None:
        """Initialize the dependency scanner runtime module."""
        self._health_check = DependencyScannerHealthCheck()
        self._log = get_logger("eaip.depscan.integration")

    @property
    def health_check(self) -> DependencyScannerHealthCheck:
        """Return the dependency scanner health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("depscan.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("depscan.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("depscan.module.stopping")


__all__ = ["DependencyScannerRuntimeModule"]
