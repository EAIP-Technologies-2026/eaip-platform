"""Platform lifecycle runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.platform_lifecycle.health import PlatformLifecycleHealthCheck
from eaip.platform_lifecycle.service import PlatformLifecycleService

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class PlatformLifecycleRuntimeModule:
    """Runtime module for the platform lifecycle manager."""

    name: str = "platform_lifecycle"

    def __init__(self) -> None:
        """Initialize the platform lifecycle runtime module."""
        self._service = PlatformLifecycleService()
        self._health_check = PlatformLifecycleHealthCheck()
        self._log = get_logger("eaip.platform_lifecycle.integration")

    @property
    def service(self) -> PlatformLifecycleService:
        """Return the lifecycle service instance."""
        return self._service

    @property
    def health_check(self) -> PlatformLifecycleHealthCheck:
        """Return the health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("platform_lifecycle.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("platform_lifecycle.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("platform_lifecycle.module.stopping")


__all__ = ["PlatformLifecycleRuntimeModule"]
