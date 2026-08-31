"""Export compliance runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.exportcheck.health import ExportComplianceHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ExportComplianceRuntimeModule:
    """Runtime module for export compliance."""

    name: str = "exportcheck"

    def __init__(self) -> None:
        self._health_check = ExportComplianceHealthCheck()
        self._log = get_logger("eaip.exportcheck.integration")

    @property
    def health_check(self) -> ExportComplianceHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("exportcheck.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("exportcheck.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("exportcheck.module.stopping")


__all__ = ["ExportComplianceRuntimeModule"]
