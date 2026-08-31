"""Data catalog runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.datacatalog.health import DataCatalogHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class DataCatalogRuntimeModule:
    """Runtime module for the data catalog."""

    name: str = "datacatalog"

    def __init__(self) -> None:
        """Initialize the data catalog runtime module."""
        self._health_check = DataCatalogHealthCheck()
        self._log = get_logger("eaip.datacatalog.integration")

    @property
    def health_check(self) -> DataCatalogHealthCheck:
        """Return the data catalog health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("datacatalog.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("datacatalog.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("datacatalog.module.stopping")


__all__ = ["DataCatalogRuntimeModule"]
