"""Integration layer — FileStoreRuntimeModule for kernel lifecycle."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.filestore.asset_manager import AssetManager
from eaip.filestore.health import FileStoreHealthCheck
from eaip.health.checks import HealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class FileStoreRuntimeModule:
    """RuntimeModule that bootstraps the File Store subsystem during kernel start."""

    name: str = "filestore"

    def __init__(self, asset_manager: AssetManager | None = None) -> None:
        """Initialize with optional asset manager."""
        self._asset_manager = asset_manager or AssetManager()
        self._started = False
        self._startup_duration: float = 0.0
        self._log = get_logger("eaip.filestore.integration")

    @property
    def asset_manager(self) -> AssetManager:
        """Return the asset manager."""
        return self._asset_manager

    @property
    def startup_duration(self) -> float:
        """Return the startup duration in seconds."""
        return self._startup_duration

    async def start(self, kernel: RuntimeKernel | None = None) -> None:
        """Start the module and register health check."""
        t0 = time.monotonic()
        self._log.info("filestore.integration.start")

        if kernel is not None:
            kernel.platform.health.register(self._health_check())

        self._startup_duration = time.monotonic() - t0
        self._started = True
        self._log.info(
            "filestore.integration.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel | None = None) -> None:
        """Stop the module."""
        self._log.info("filestore.integration.stop")
        self._started = False

    def _health_check(self) -> HealthCheck:
        """Create a health check instance."""
        asset_count = len(self._asset_manager.list_items())
        return FileStoreHealthCheck(asset_count=asset_count, provider_available=True)


__all__ = ["FileStoreRuntimeModule"]
