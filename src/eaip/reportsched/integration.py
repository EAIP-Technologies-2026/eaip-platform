"""Report scheduler runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.reportsched.health import ReportSchedulerHealthCheck

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ReportSchedulerRuntimeModule:
    """Runtime module for report scheduling."""

    name: str = "reportsched"

    def __init__(self) -> None:
        """Initialize the report scheduler runtime module."""
        self._health_check = ReportSchedulerHealthCheck()
        self._log = get_logger("eaip.reportsched.integration")

    @property
    def health_check(self) -> ReportSchedulerHealthCheck:
        """Return the report scheduler health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("reportsched.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("reportsched.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("reportsched.module.stopping")


__all__ = ["ReportSchedulerRuntimeModule"]
