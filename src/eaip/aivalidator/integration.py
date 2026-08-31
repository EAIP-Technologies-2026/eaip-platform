"""AI validator runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.aivalidator.health import AIValidatorHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class AIValidatorRuntimeModule:
    """Runtime module for AI validation."""

    name: str = "aivalidator"

    def __init__(self) -> None:
        """Initialize the AI validator runtime module."""
        self._health_check = AIValidatorHealthCheck()
        self._log = get_logger("eaip.aivalidator.integration")

    @property
    def health_check(self) -> AIValidatorHealthCheck:
        """Return the AI validator health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("aivalidator.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("aivalidator.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("aivalidator.module.stopping")


__all__ = ["AIValidatorRuntimeModule"]
