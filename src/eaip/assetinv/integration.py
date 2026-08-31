"""Asset inventory runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.assetinv.health import AssetInventoryHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class AssetInventoryRuntimeModule:
    """Runtime module for asset inventory management."""

    name: str = "assetinv"

    def __init__(self) -> None:
        """Initialize the asset inventory runtime module."""
        self._health_check = AssetInventoryHealthCheck()
        self._log = get_logger("eaip.assetinv.integration")

    @property
    def health_check(self) -> AssetInventoryHealthCheck:
        """Return the asset inventory health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("assetinv.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("assetinv.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("assetinv.module.stopping")


__all__ = ["AssetInventoryRuntimeModule"]
