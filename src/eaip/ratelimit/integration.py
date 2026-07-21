"""Rate limiting runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.ratelimit.health import RateLimitHealthCheck

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class RateLimitRuntimeModule:
    """Runtime module for rate limiting."""

    name: str = "ratelimit"

    def __init__(self) -> None:
        """Initialize the rate limit runtime module."""
        self._health_check = RateLimitHealthCheck()
        self._log = get_logger("eaip.ratelimit.integration")

    @property
    def health_check(self) -> RateLimitHealthCheck:
        """Return the rate limit health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("ratelimit.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("ratelimit.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("ratelimit.module.stopping")


__all__ = ["RateLimitRuntimeModule"]
