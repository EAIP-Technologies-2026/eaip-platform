"""Runtime module integration for the admin_api subsystem."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.admin_api.health import AdminApiHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class AdminApiRuntimeModule:
    """RuntimeModule that registers the admin API subsystem into the kernel.

    On start, registers admin API health checks. On stop, performs
    cleanup of admin API resources.
    """

    name: str = "admin_api"

    def __init__(self, health_check: AdminApiHealthCheck | None = None) -> None:
        """Initialize AdminApiRuntimeModule.

        Args:
            health_check: An optional AdminApiHealthCheck instance.
        """
        self._health_check = health_check or AdminApiHealthCheck()
        self._log = get_logger("eaip.admin_api.integration")
        self._started: bool = False

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register admin API health checks into the kernel's platform.

        Args:
            kernel: The runtime kernel.
        """
        platform = kernel.platform
        platform.health.register(self._health_check)
        self._started = True
        self._log.info("admin_api.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:  # noqa: ARG002
        """Clean up admin API resources on shutdown.

        Args:
            kernel: The runtime kernel.
        """
        self._started = False
        self._log.info("admin_api.module.stopped")

    @property
    def started(self) -> bool:
        """Return whether the module has been started."""
        return self._started


__all__ = ["AdminApiRuntimeModule"]
