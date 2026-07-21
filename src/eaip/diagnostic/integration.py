"""Diagnostic data collector runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.diagnostic.health import DiagnosticHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class DiagnosticRuntimeModule:
    """Runtime module for the diagnostic data collector."""

    name: str = "diagnostic"

    def __init__(self) -> None:
        """Initialize the diagnostic runtime module."""
        self._health_check = DiagnosticHealthCheck()
        self._log = get_logger("eaip.diagnostic.integration")

    @property
    def health_check(self) -> DiagnosticHealthCheck:
        """Return the diagnostic health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("diagnostic.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("diagnostic.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("diagnostic.module.stopping")


__all__ = ["DiagnosticRuntimeModule"]
