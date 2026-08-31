"""Runtime module integration for the organization subsystem."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.organization.health import OrganizationHealthCheck

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class OrganizationRuntimeModule:
    """RuntimeModule that registers the organization subsystem into the kernel.

    On start, registers organization health checks. On stop, performs
    cleanup of organization resources.
    """

    name: str = "organization"

    def __init__(self, health_check: OrganizationHealthCheck | None = None) -> None:
        """Initialize OrganizationRuntimeModule."""
        self._health_check = health_check or OrganizationHealthCheck()
        self._log = get_logger("eaip.organization.integration")
        self._started: bool = False

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register organization health checks into the kernel's platform.

        Args:
            kernel: The runtime kernel.
        """
        platform = kernel.platform
        platform.health.register(self._health_check)
        self._started = True
        self._log.info("organization.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:  # noqa: ARG002
        """Clean up organization resources on shutdown.

        Args:
            kernel: The runtime kernel.
        """
        self._started = False
        self._log.info("organization.module.stopped")

    @property
    def started(self) -> bool:
        """Return whether the module has been started."""
        return self._started
