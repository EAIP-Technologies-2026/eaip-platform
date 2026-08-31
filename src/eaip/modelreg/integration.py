"""Model registry runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.modelreg.health import ModelRegistryHealthCheck

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ModelRegistryRuntimeModule:
    """Runtime module for the model registry."""

    name: str = "modelreg"

    def __init__(self) -> None:
        """Initialize the model registry runtime module."""
        self._health_check = ModelRegistryHealthCheck()
        self._log = get_logger("eaip.modelreg.integration")

    @property
    def health_check(self) -> ModelRegistryHealthCheck:
        """Return the model registry health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("modelreg.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("modelreg.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("modelreg.module.stopping")


__all__ = ["ModelRegistryRuntimeModule"]
