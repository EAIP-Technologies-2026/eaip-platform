"""Runtime module integration for the department management subsystem."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.department_management.health import DepartmentManagementHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class DepartmentManagementRuntimeModule:
    """RuntimeModule that registers the department management subsystem into the kernel.

    On start, registers health checks. On stop, performs cleanup.
    """

    name: str = "department_management"

    def __init__(self, health_check: DepartmentManagementHealthCheck | None = None) -> None:
        """Initialize DepartmentManagementRuntimeModule.

        Args:
            health_check: An optional DepartmentManagementHealthCheck instance.
        """
        self._health_check = health_check or DepartmentManagementHealthCheck()
        self._log = get_logger("eaip.department_management.integration")
        self._started: bool = False

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register department management health checks into the kernel's platform.

        Args:
            kernel: The runtime kernel.
        """
        platform = kernel.platform
        platform.health.register(self._health_check)
        self._started = True
        self._log.info("department_management.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:  # noqa: ARG002
        """Clean up department management resources on shutdown.

        Args:
            kernel: The runtime kernel.
        """
        self._started = False
        self._log.info("department_management.module.stopped")

    @property
    def started(self) -> bool:
        """Return whether the module has been started."""
        return self._started
