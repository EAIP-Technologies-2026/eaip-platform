"""Diagnostics runtime module for kernel lifecycle."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.diagnostics.health import DiagnosticsHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class DiagnosticsRuntimeModule:
    name: str = "diagnostics"

    def __init__(self) -> None:
        self._health_check = DiagnosticsHealthCheck()
        self._log = get_logger("eaip.diagnostics.integration")

    @property
    def health_check(self) -> DiagnosticsHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("diagnostics.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("diagnostics.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("diagnostics.module.stopping")


__all__ = ["DiagnosticsRuntimeModule"]
