"""Integration layer — HealthRptRuntimeModule for kernel lifecycle."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.healthrpt.health import HealthRptHealthCheck
from eaip.healthrpt.reporter import HealthReporter
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class HealthRptRuntimeModule:
    """RuntimeModule that bootstraps the enterprise health reporter subsystem."""

    name: str = "healthrpt"

    def __init__(self, reporter: HealthReporter | None = None) -> None:
        self._reporter = reporter or HealthReporter()
        self._log = get_logger("eaip.healthrpt.integration")

    @property
    def reporter(self) -> HealthReporter:
        return self._reporter

    async def start(self, kernel: RuntimeKernel) -> None:
        """Start the enterprise health reporter module."""
        self._log.info("healthrpt.module.starting")
        components = await self._reporter.list_components()
        health_check = HealthRptHealthCheck(
            component_count=len(components),
            report_count=0,
        )
        kernel.platform.health.register(health_check)
        self._log.info("healthrpt.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the enterprise health reporter module."""
        self._log.info("healthrpt.module.stopping")


__all__ = ["HealthRptRuntimeModule"]
