"""Event retention manager runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.eventret.health import EventRetentionHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class EventRetentionRuntimeModule:
    """Runtime module for event retention management."""

    name: str = "eventret"

    def __init__(self) -> None:
        """Initialize the event retention runtime module."""
        self._health_check = EventRetentionHealthCheck()
        self._log = get_logger("eaip.eventret.integration")

    @property
    def health_check(self) -> EventRetentionHealthCheck:
        """Return the event retention health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("eventret.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("eventret.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("eventret.module.stopping")


__all__ = ["EventRetentionRuntimeModule"]
