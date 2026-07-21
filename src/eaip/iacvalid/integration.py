"""IaC validator runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.iacvalid.health import IaCValidatorHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class IaCValidatorRuntimeModule:
    """Runtime module for Infrastructure as Code validation."""

    name: str = "iacvalid"

    def __init__(self) -> None:
        """Initialize the runtime module."""
        self._health_check = IaCValidatorHealthCheck()
        self._log = get_logger("eaip.iacvalid.integration")

    @property
    def health_check(self) -> IaCValidatorHealthCheck:
        """Return the health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("iacvalid.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("iacvalid.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("iacvalid.module.stopping")


__all__ = ["IaCValidatorRuntimeModule"]
