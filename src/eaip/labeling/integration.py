"""Data labeling runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.labeling.health import LabelingHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class LabelingRuntimeModule:
    """Runtime module for data labeling."""

    name: str = "labeling"

    def __init__(self) -> None:
        """Initialize the labeling runtime module."""
        self._health_check = LabelingHealthCheck()
        self._log = get_logger("eaip.labeling.integration")

    @property
    def health_check(self) -> LabelingHealthCheck:
        """Return the labeling health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("labeling.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("labeling.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("labeling.module.stopping")


__all__ = ["LabelingRuntimeModule"]
