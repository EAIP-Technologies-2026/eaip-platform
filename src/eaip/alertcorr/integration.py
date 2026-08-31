"""Alert correlation runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.alertcorr.health import AlertCorrelationHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class AlertCorrelationRuntimeModule:
    """Runtime module for the alert correlator."""

    name: str = "alertcorr"

    def __init__(self) -> None:
        """Initialize the alert correlation runtime module."""
        self._health_check = AlertCorrelationHealthCheck()
        self._log = get_logger("eaip.alertcorr.integration")

    @property
    def health_check(self) -> AlertCorrelationHealthCheck:
        """Return the alert correlation health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("alertcorr.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("alertcorr.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("alertcorr.module.stopping")


__all__ = ["AlertCorrelationRuntimeModule"]
