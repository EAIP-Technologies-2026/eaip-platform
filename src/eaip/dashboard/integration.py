"""Dashboard builder runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.dashboard.health import DashboardHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class DashboardRuntimeModule:
    name: str = "dashboard"

    def __init__(self) -> None:
        self._health_check = DashboardHealthCheck()
        self._log = get_logger("eaip.dashboard.integration")

    @property
    def health_check(self) -> DashboardHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("dashboard.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("dashboard.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("dashboard.module.stopping")


__all__ = ["DashboardRuntimeModule"]
