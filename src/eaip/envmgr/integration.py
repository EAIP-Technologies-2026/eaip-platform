"""Environment variable manager runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.envmgr.health import EnvMgrHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class EnvMgrRuntimeModule:
    """Runtime module for environment variable management."""

    name: str = "envmgr"

    def __init__(self) -> None:
        """Initialize the environment variable manager runtime module."""
        self._health_check = EnvMgrHealthCheck()
        self._log = get_logger("eaip.envmgr.integration")

    @property
    def health_check(self) -> EnvMgrHealthCheck:
        """Return the environment variable manager health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("envmgr.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("envmgr.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("envmgr.module.stopping")


__all__ = ["EnvMgrRuntimeModule"]
