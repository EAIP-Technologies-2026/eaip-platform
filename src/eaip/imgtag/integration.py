"""Image tag manager runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.imgtag.health import ImageTagManagerHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ImageTagManagerRuntimeModule:
    """Runtime module for image tag management."""

    name: str = "imgtag"

    def __init__(self) -> None:
        """Initialize the runtime module."""
        self._health_check = ImageTagManagerHealthCheck()
        self._log = get_logger("eaip.imgtag.integration")

    @property
    def health_check(self) -> ImageTagManagerHealthCheck:
        """Return the health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("imgtag.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("imgtag.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("imgtag.module.stopping")


__all__ = ["ImageTagManagerRuntimeModule"]
