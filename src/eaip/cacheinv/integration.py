"""Cache invalidation runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.cacheinv.health import CacheInvalidationHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class CacheInvalidationRuntimeModule:
    """Runtime module for the cache invalidator."""

    name: str = "cacheinv"

    def __init__(self) -> None:
        """Initialize the cache invalidation runtime module."""
        self._health_check = CacheInvalidationHealthCheck()
        self._log = get_logger("eaip.cacheinv.integration")

    @property
    def health_check(self) -> CacheInvalidationHealthCheck:
        """Return the cache invalidation health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("cacheinv.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("cacheinv.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("cacheinv.module.stopping")


__all__ = ["CacheInvalidationRuntimeModule"]
