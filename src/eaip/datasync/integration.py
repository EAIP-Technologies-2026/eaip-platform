"""Data synchronization runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.datasync.health import DataSyncHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class DataSyncRuntimeModule:
    """Runtime module for data synchronization management."""

    name: str = "datasync"

    def __init__(self) -> None:
        """Initialize the data synchronization runtime module."""
        self._health_check = DataSyncHealthCheck()
        self._log = get_logger("eaip.datasync.integration")

    @property
    def health_check(self) -> DataSyncHealthCheck:
        """Return the data sync health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("datasync.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("datasync.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("datasync.module.stopping")


__all__ = ["DataSyncRuntimeModule"]
