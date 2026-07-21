"""Runtime module integration for the operations subsystem."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.operations.health import OperationsHealthCheck

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class OperationsRuntimeModule:
    """RuntimeModule that registers the operations subsystem into the kernel.

    On start, registers operations health checks. On stop, performs
    cleanup of operations resources.
    """

    name: str = "operations"

    def __init__(self, health_check: OperationsHealthCheck | None = None) -> None:
        """Initialize OperationsRuntimeModule.

        Args:
            health_check: An optional OperationsHealthCheck instance.
        """
        self._health_check = health_check or OperationsHealthCheck()
        self._log = get_logger("eaip.operations.integration")
        self._started: bool = False

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register operations health checks into the kernel's platform.

        Args:
            kernel: The runtime kernel.
        """
        platform = kernel.platform
        platform.health.register(self._health_check)
        self._started = True
        self._log.info("operations.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        """Clean up operations resources on shutdown.

        Args:
            kernel: The runtime kernel.
        """
        self._started = False
        self._log.info("operations.module.stopped")

    @property
    def started(self) -> bool:
        """Return whether the module has been started."""
        return self._started


__all__ = ["OperationsRuntimeModule"]
