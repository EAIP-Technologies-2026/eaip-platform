"""Runtime module integration for the Developer API & SDK Platform."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.devplatform.health import DevPlatformHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class DevPlatformRuntimeModule:
    """RuntimeModule that registers the developer platform subsystem into the kernel.

    On start, registers developer platform health checks. On stop, performs
    cleanup of developer platform resources.
    """

    name: str = "devplatform"

    def __init__(self, health_check: DevPlatformHealthCheck | None = None) -> None:
        """Initialize DevPlatformRuntimeModule.

        Args:
            health_check: An optional DevPlatformHealthCheck instance.
        """
        self._health_check = health_check or DevPlatformHealthCheck()
        self._log = get_logger("eaip.devplatform.integration")
        self._started: bool = False

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register developer platform health checks into the kernel's platform.

        Args:
            kernel: The runtime kernel.
        """
        platform = kernel.platform
        platform.health.register(self._health_check)
        self._started = True
        self._log.info("devplatform.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:  # noqa: ARG002
        """Clean up developer platform resources on shutdown.

        Args:
            kernel: The runtime kernel.
        """
        self._started = False
        self._log.info("devplatform.module.stopped")

    @property
    def started(self) -> bool:
        """Return whether the module has been started."""
        return self._started


__all__ = ["DevPlatformRuntimeModule"]
