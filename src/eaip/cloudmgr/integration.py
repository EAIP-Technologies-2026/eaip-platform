"""Cloud resource manager runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.cloudmgr.health import CloudManagerHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class CloudManagerRuntimeModule:
    """Runtime module for the cloud resource manager."""

    name: str = "cloudmgr"

    def __init__(self) -> None:
        """Initialize the cloud manager runtime module."""
        self._health_check = CloudManagerHealthCheck()
        self._log = get_logger("eaip.cloudmgr.integration")

    @property
    def health_check(self) -> CloudManagerHealthCheck:
        """Return the cloud manager health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("cloudmgr.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("cloudmgr.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("cloudmgr.module.stopping")


__all__ = ["CloudManagerRuntimeModule"]
