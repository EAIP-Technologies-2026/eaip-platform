"""Runtime diagnostics runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.runtime_diagnostics.health import RuntimeDiagnosticsHealthCheck
from eaip.runtime_diagnostics.service import RuntimeDiagnosticsService

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class RuntimeDiagnosticsRuntimeModule:
    """Runtime module for the runtime diagnostics service."""

    name: str = "runtime_diagnostics"

    def __init__(
        self,
        service: RuntimeDiagnosticsService | None = None,
    ) -> None:
        """Initialize the runtime diagnostics runtime module."""
        self._service = service or RuntimeDiagnosticsService()
        self._health_check = RuntimeDiagnosticsHealthCheck()
        self._log = get_logger("eaip.runtime_diagnostics.integration")

    @property
    def service(self) -> RuntimeDiagnosticsService:
        """Return the runtime diagnostics service instance."""
        return self._service

    @property
    def health_check(self) -> RuntimeDiagnosticsHealthCheck:
        """Return the runtime diagnostics health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("runtime_diagnostics.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("runtime_diagnostics.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("runtime_diagnostics.module.stopping")


__all__ = ["RuntimeDiagnosticsRuntimeModule"]
