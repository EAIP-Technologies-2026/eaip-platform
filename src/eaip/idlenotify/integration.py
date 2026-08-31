"""Idle resource notifier runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.idlenotify.health import IdleResourceNotifierHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class IdleResourceNotifierRuntimeModule:
    """Runtime module for idle resource notification."""

    name: str = "idlenotify"

    def __init__(self) -> None:
        """Initialize the runtime module."""
        self._health_check = IdleResourceNotifierHealthCheck()
        self._log = get_logger("eaip.idlenotify.integration")

    @property
    def health_check(self) -> IdleResourceNotifierHealthCheck:
        """Return the health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("idlenotify.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("idlenotify.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("idlenotify.module.stopping")


__all__ = ["IdleResourceNotifierRuntimeModule"]
