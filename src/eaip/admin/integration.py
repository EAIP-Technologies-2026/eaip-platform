"""Runtime module integration for the admin subsystem."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.admin.health import AdminHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class AdminRuntimeModule:
    """RuntimeModule that registers the admin subsystem into the kernel.

    On start, registers admin health checks. On stop, performs
    cleanup of admin resources.
    """

    name: str = "admin"

    def __init__(self, health_check: AdminHealthCheck | None = None) -> None:
        """Initialize AdminRuntimeModule.

        Args:
            health_check: An optional AdminHealthCheck instance.
        """
        self._health_check = health_check or AdminHealthCheck()
        self._log = get_logger("eaip.admin.integration")
        self._started: bool = False

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register admin health checks into the kernel's platform.

        Args:
            kernel: The runtime kernel.
        """
        platform = kernel.platform
        platform.health.register(self._health_check)
        self._started = True
        self._log.info("admin.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:  # noqa: ARG002
        """Clean up admin resources on shutdown.

        Args:
            kernel: The runtime kernel.
        """
        self._started = False
        self._log.info("admin.module.stopped")

    @property
    def started(self) -> bool:
        """Return whether the module has been started."""
        return self._started
