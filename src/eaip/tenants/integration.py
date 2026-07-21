"""Runtime module integration for the tenant subsystem."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.tenants.health import TenantHealthCheck

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class TenantRuntimeModule:
    """RuntimeModule that registers the tenant subsystem into the kernel.

    On start, registers tenant health checks. On stop, performs
    cleanup of tenant resources.
    """

    name: str = "tenants"

    def __init__(self, health_check: TenantHealthCheck | None = None) -> None:
        self._health_check = health_check or TenantHealthCheck()
        self._log = get_logger("eaip.tenants.integration")
        self._started: bool = False

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register tenant health checks into the kernel's platform.

        Args:
            kernel: The runtime kernel.
        """
        platform = kernel.platform
        platform.health.register(self._health_check)
        self._started = True
        self._log.info("tenants.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        """Clean up tenant resources on shutdown.

        Args:
            kernel: The runtime kernel.
        """
        self._started = False
        self._log.info("tenants.module.stopped")

    @property
    def started(self) -> bool:
        """Return whether the module has been started."""
        return self._started
