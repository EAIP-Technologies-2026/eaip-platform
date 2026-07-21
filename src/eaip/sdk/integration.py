"""Runtime module integration for the SDK subsystem."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.sdk.health import SdkHealthCheck

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class SdkRuntimeModule:
    """RuntimeModule that registers the SDK subsystem into the kernel.

    On start, registers SDK health checks. On stop, performs
    cleanup of SDK resources.
    """

    name: str = "sdk"

    def __init__(self, health_check: SdkHealthCheck | None = None) -> None:
        """Initialize SdkRuntimeModule.

        Args:
            health_check: An optional SdkHealthCheck instance.
        """
        self._health_check = health_check or SdkHealthCheck()
        self._log = get_logger("eaip.sdk.integration")
        self._started: bool = False

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register SDK health checks into the kernel's platform.

        Args:
            kernel: The runtime kernel.
        """
        platform = kernel.platform
        platform.health.register(self._health_check)
        self._started = True
        self._log.info("sdk.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:  # noqa: ARG002
        """Clean up SDK resources on shutdown.

        Args:
            kernel: The runtime kernel.
        """
        self._started = False
        self._log.info("sdk.module.stopped")

    @property
    def started(self) -> bool:
        """Return whether the module has been started."""
        return self._started
