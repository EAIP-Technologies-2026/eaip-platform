"""Deployment rollback runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.rollbackmgr.health import RollbackManagerHealthCheck

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class RollbackManagerRuntimeModule:
    """Runtime module for deployment rollback management."""

    name: str = "rollbackmgr"

    def __init__(self) -> None:
        """Initialize the rollback manager runtime module."""
        self._health_check = RollbackManagerHealthCheck()
        self._log = get_logger("eaip.rollbackmgr.integration")

    @property
    def health_check(self) -> RollbackManagerHealthCheck:
        """Return the rollback manager health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("rollbackmgr.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("rollbackmgr.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("rollbackmgr.module.stopping")


__all__ = ["RollbackManagerRuntimeModule"]
