"""Batch job scheduler runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.batchjob.health import BatchJobSchedulerHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class BatchJobRuntimeModule:
    """Runtime module for the batch job scheduler."""

    name: str = "batchjob"

    def __init__(self) -> None:
        """Initialize the batch job runtime module."""
        self._health_check = BatchJobSchedulerHealthCheck()
        self._log = get_logger("eaip.batchjob.integration")

    @property
    def health_check(self) -> BatchJobSchedulerHealthCheck:
        """Return the batch job health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("batchjob.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("batchjob.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("batchjob.module.stopping")


__all__ = ["BatchJobRuntimeModule"]
