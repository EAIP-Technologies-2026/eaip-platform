"""Rate limiting runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.throttle.health import ThrottleHealthCheck

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ThrottleRuntimeModule:
    """Runtime module for rate limiting."""

    name: str = "throttle"

    def __init__(self) -> None:
        """Initialize the throttle runtime module."""
        self._health_check = ThrottleHealthCheck()
        self._log = get_logger("eaip.throttle.integration")

    @property
    def health_check(self) -> ThrottleHealthCheck:
        """Return the throttle health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("throttle.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("throttle.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("throttle.module.stopping")


__all__ = ["ThrottleRuntimeModule"]
