"""Resource quota runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.resquota.health import QuotaHealthCheck

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class QuotaRuntimeModule:
    """Runtime module for resource quota management."""

    name: str = "resquota"

    def __init__(self) -> None:
        """Initialize the quota runtime module."""
        self._health_check = QuotaHealthCheck()
        self._log = get_logger("eaip.resquota.integration")

    @property
    def health_check(self) -> QuotaHealthCheck:
        """Return the quota health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("resquota.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("resquota.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("resquota.module.stopping")


__all__ = ["QuotaRuntimeModule"]
